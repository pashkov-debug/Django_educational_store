
var mix = {
  computed: {
    totalCost() {
      return Number(this.totalCostRaw || 0)
    }
  },
  methods: {
    resolveOrderId() {
      if (location.pathname.startsWith('/orders/')) {
        return Number(location.pathname.replace('/orders/', '').replace('/', ''))
      }
      if (location.pathname.startsWith('/order-detail/')) {
        return Number(location.pathname.replace('/order-detail/', '').replace('/', ''))
      }
      return null
    },
    getOrder(orderId) {
      if (typeof orderId !== 'number' || Number.isNaN(orderId)) return
      this.getData(`/api/order/${orderId}/`)
        .then(data => {
          this.orderId = data.id
          this.createdAt = data.createdAt
          this.fullName = data.fullName
          this.phone = data.phone
          this.email = data.email
          this.deliveryType = data.deliveryType
          this.city = data.city
          this.address = data.address
          this.paymentType = data.paymentType
          this.status = data.status
          this.totalCostRaw = data.totalCost
          this.products = data.products || []
          this.paymentError = typeof data.paymentError !== 'undefined' ? data.paymentError : null
        })
    },
    confirmOrder() {
      if (this.orderId !== null) {
        this.postData(`/api/order/${this.orderId}/`, {
          fullName: this.fullName,
          phone: this.phone,
          email: this.email,
          deliveryType: this.deliveryType,
          city: this.city,
          address: this.address,
          paymentType: this.paymentType,
        })
          .then(({ data: { orderId } }) => {
            location.replace(`/payment/${orderId}/`)
          })
          .catch((error) => {
            alert(error.message)
          })
      }
    },
    auth() {
      const username = document.querySelector('#username').value
      const password = document.querySelector('#password').value
      this.postData('/api/sign-in/', { username, password })
        .then(() => {
          location.assign(`/orders/${this.orderId}/`)
        })
        .catch((error) => {
          alert(error.message)
        })
    }
  },
  mounted() {
    const orderId = this.resolveOrderId()
    this.orderId = orderId && !Number.isNaN(orderId) ? orderId : null
    if (this.orderId) this.getOrder(this.orderId)
  },
  data() {
    return {
      orderId: null,
      createdAt: null,
      fullName: '',
      phone: '',
      email: '',
      deliveryType: 'delivery',
      city: '',
      address: '',
      paymentType: 'card',
      status: null,
      totalCostRaw: 0,
      products: [],
      paymentError: null,
    }
  },
}
