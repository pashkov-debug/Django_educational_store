
var mix = {
  methods: {
    signIn() {
      const username = document.querySelector('#login').value
      const password = document.querySelector('#password').value
      this.postData('/api/sign-in/', { username, password })
        .then(() => {
          location.assign('/')
        })
        .catch((error) => {
          alert(error.message)
        })
    }
  }
}
