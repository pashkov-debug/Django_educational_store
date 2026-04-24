import time

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from shopapp.models import Order, Payment


class Command(BaseCommand):
    help = "Обрабатывает ожидающие платежи учебного магазина."

    def add_arguments(self, parser):
        parser.add_argument(
            "--loop",
            action="store_true",
            help="Запустить обработку в бесконечном цикле.",
        )
        parser.add_argument(
            "--sleep",
            type=float,
            default=5.0,
            help="Пауза между итерациями при --loop.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Максимум платежей за одну итерацию.",
        )

    def handle(self, *args, **options):
        if options["loop"]:
            self.stdout.write("Запущен worker обработки платежей.")
            while True:
                processed_count = self.process_once(limit=options["limit"])
                self.stdout.write(f"Обработано платежей: {processed_count}")
                time.sleep(options["sleep"])

        processed_count = self.process_once(limit=options["limit"])
        self.stdout.write(self.style.SUCCESS(f"Обработано платежей: {processed_count}"))

    def process_once(self, *, limit: int) -> int:
        payment_ids = list(
            Payment.objects.filter(status=Payment.Status.PENDING)
            .order_by("created_at")
            .values_list("pk", flat=True)[:limit]
        )

        processed_count = 0

        for payment_id in payment_ids:
            with transaction.atomic():
                payment = (
                    Payment.objects.select_for_update()
                    .select_related("order")
                    .filter(pk=payment_id, status=Payment.Status.PENDING)
                    .first()
                )

                if payment is None:
                    continue

                self.process_payment(payment)
                processed_count += 1

        return processed_count

    def process_payment(self, payment: Payment) -> None:
        account_number = payment.account_number
        is_success = int(account_number) % 2 == 0 and not account_number.endswith("0")

        payment.processed_at = timezone.now()

        if is_success:
            payment.status = Payment.Status.PAID
            payment.error_message = ""
            payment.save(update_fields=("status", "error_message", "processed_at"))

            payment.order.payment_status = Order.PaymentStatus.PAID
            payment.order.payment_error = ""
            payment.order.status = "paid"
            payment.order.save(update_fields=("payment_status", "payment_error", "status"))
            return

        payment.status = Payment.Status.FAILED
        payment.error_message = "Платёж отклонён тестовым платёжным сервисом."
        payment.save(update_fields=("status", "error_message", "processed_at"))

        payment.order.payment_status = Order.PaymentStatus.FAILED
        payment.order.payment_error = payment.error_message
        payment.order.status = "payment_failed"
        payment.order.save(update_fields=("payment_status", "payment_error", "status"))