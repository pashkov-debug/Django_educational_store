
var mix = {
  methods: {
    setTag(id) {
      this.topTags = this.topTags.map(tag => tag.id === id ? { ...tag, selected: !tag.selected } : tag)
      this.getCatalogs()
    },
    setSort(id) {
      if (this.selectedSort?.id === id) {
        this.selectedSort.selected = this.selectedSort.selected === 'dec' ? 'inc' : 'dec'
      } else {
        this.selectedSort = { ...(this.sortRules.find(sort => sort.id === id) || this.sortRules[0]), selected: 'dec' }
      }
      this.getCatalogs()
    },
    getTags() {
      this.getData('/api/tags/', { category: this.category })
        .then(data => {
          this.topTags = (data || []).map(tag => ({ ...tag, selected: false }))
        })
        .catch(() => {
          this.topTags = []
        })
    },
    getCatalogs(page = 1) {
      const PAGE_LIMIT = 20
      const tags = this.topTags.filter(tag => !!tag.selected).map(tag => tag.id)
      this.getData('/api/catalog/', {
        currentPage: page,
        category: this.category,
        sort: this.selectedSort ? this.selectedSort.id : null,
        sortType: this.selectedSort ? this.selectedSort.selected : null,
        tags,
        limit: PAGE_LIMIT,
        filter: JSON.stringify(this.filter),
      }).then(data => {
        this.catalogCards = data.items || []
        this.currentPage = data.currentPage || 1
        this.lastPage = data.lastPage || 1
      }).catch(() => {})
    }
  },
  mounted() {
    this.selectedSort = this.sortRules?.[1] ? { ...this.sortRules?.[1], selected: 'inc' } : null
    const path = location.pathname.replace(/^\/catalog\/?/, '').replace(/\/$/, '')
    this.category = path.length && !isNaN(Number(path)) ? Number(path) : null

    const params = new URLSearchParams(location.search)
    this.filter.name = params.get('q') || params.get('filter') || ''

    this.getCatalogs()
    this.getTags()
  },
  data() {
    return {
      category: null,
      catalogCards: [],
      currentPage: 1,
      lastPage: 1,
      selectedSort: null,
      filter: {
        name: '',
        minPrice: 0,
        maxPrice: 50000,
        freeDelivery: false,
        available: true,
      }
    }
  }
}
