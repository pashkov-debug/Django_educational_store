
const { createApp } = Vue

createApp({
  delimiters: ['${', '}$'],
  mixins: [window.mix ? window.mix : {}],
  methods: {
    getCookie(name) {
      let cookieValue = null
      if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';')
        for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim()
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
            break
          }
        }
      }
      return cookieValue
    },
    async postData(url, payload = {}, headers = {}) {
      try {
        const response = await axios.post(url, payload, {
          headers: {
            'X-CSRFToken': this.getCookie('csrftoken'),
            ...(headers || {}),
          }
        })
        return { data: response.data, status: response.status }
      } catch (error) {
        const message = error?.response?.data?.error || `Request failed: ${url}`
        console.warn(message)
        throw new Error(message)
      }
    },
    async getData(url, payload) {
      try {
        const response = await axios.get(url, { params: payload })
        return response.data
      } catch (error) {
        const message = error?.response?.data?.error || `GET request failed: ${url}`
        console.warn(message)
        throw new Error(message)
      }
    },
    search() {
      const query = (this.searchText || '').trim()
      location.assign(query ? `/catalog/?q=${encodeURIComponent(query)}` : '/catalog/')
    },
    getCategories() {
      this.getData('/api/categories/')
        .then(data => {
          this.categories = Array.isArray(data) ? data : []
        })
        .catch(() => {
          this.categories = []
        })
    },
    getBasket() {
      this.getData('/api/basket/')
        .then(data => {
          const basket = {}
          ;(data || []).forEach(item => {
            basket[item.id] = { ...item }
          })
          this.basket = basket
        })
        .catch(() => {
          this.basket = {}
        })
    },
    addToBasket(item, count = 1) {
      const { id } = item
      this.postData('/api/basket/', { id, count })
        .then(() => this.getBasket())
        .catch(() => {})
    },
    removeFromBasket(id, count) {
      axios.delete('/api/basket/', {
        data: { id, count },
        headers: {
          'X-CSRFToken': this.getCookie('csrftoken'),
        }
      }).then(() => {
        this.getBasket()
      }).catch(() => {
        console.warn('Cannot remove from basket')
      })
    },
    signOut() {
      this.postData('/api/sign-out/')
        .finally(() => location.assign('/'))
    }
  },
  computed: {
    basketCount() {
      return Object.values(this.basket || {}).reduce((acc, { count, price }) => {
        acc.count += Number(count || 0)
        acc.price += Number(count || 0) * Number(price || 0)
        return acc
      }, { count: 0, price: 0 })
    }
  },
  data() {
    return {
      filters: {
        price: {
          minValue: 1,
          maxValue: 500000,
          currentFromValue: 1,
          currentToValue: 50000,
        },
      },
      sortRules: [
        { id: 'rating', title: 'Popularity' },
        { id: 'price', title: 'Price' },
        { id: 'reviews', title: 'Reviews' },
        { id: 'date', title: 'Newest' },
      ],
      topTags: [],
      categories: [],
      catalogFromServer: [],
      orders: [],
      cart: [],
      paymentData: {},
      basket: {},
      searchText: '',
    }
  },
  mounted() {
    this.getCategories()
    this.getBasket()
  }
}).mount('#site')
