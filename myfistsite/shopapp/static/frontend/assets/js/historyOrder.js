
var mix = {
  methods: {
    getHistoryOrder() {
      this.getData('/api/orders/')
        .then(data => {
          this.orders = data || []
        }).catch(() => {
          this.orders = []
        })
    }
  },
  mounted() {
    this.getHistoryOrder()
  },
  data() {
    return {
      orders: [],
    }
  }
}
