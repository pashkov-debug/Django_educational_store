
var mix = {
  methods: {
    generateRandomNumber() {
      let number = Math.floor(Math.random() * 100000000).toString().padStart(8, '0')
      if (Number(number) % 2 !== 0) {
        number = (Number(number) + 1).toString().padStart(8, '0').slice(0, 8)
      }
      this.number = number
    },
    submitPayment() {
      const orderId = location.pathname.startsWith('/payment/')
        ? Number(location.pathname.replace('/payment/', '').replace('/', ''))
        : null
      this.postData(`/api/payment/${orderId}/`, {
        number: this.number
      })
        .then(() => {
          alert('Payment request sent')
          location.assign('/history-order/')
        })
        .catch((error) => {
          alert(error.message)
        })
    }
  },
  data() {
    return {
      number: ''
    }
  }
}
