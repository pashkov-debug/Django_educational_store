
var mix = {
  computed: {
    tags() {
      return this.product?.tags || []
    }
  },
  methods: {
    changeCount(value) {
      this.count = this.count + value
      if (this.count < 1) this.count = 1
    },
    getProduct() {
      const productId = location.pathname.startsWith('/product/')
        ? Number(location.pathname.replace('/product/', '').replace('/', ''))
        : null
      if (!productId) return
      this.getData(`/api/product/${productId}/`).then(data => {
        this.product = { ...data }
        if (data.images?.length) this.activePhoto = 0
      }).catch(() => {
        this.product = {}
      })
    },
    submitReview() {
      this.postData(`/api/product/${this.product.id}/reviews/`, {
        author: this.review.author,
        email: this.review.email,
        text: this.review.text,
        rate: this.review.rate
      }).then(({ data }) => {
        this.product.reviews = data
        alert('Review published')
        this.review = { author: '', email: '', text: '', rate: 5 }
      }).catch((error) => {
        alert(error.message)
      })
    },
    setActivePhoto(index) {
      this.activePhoto = index
    }
  },
  mounted() {
    this.getProduct()
  },
  data() {
    return {
      product: {},
      activePhoto: 0,
      count: 1,
      review: {
        author: '',
        email: '',
        text: '',
        rate: 5
      }
    }
  }
}
