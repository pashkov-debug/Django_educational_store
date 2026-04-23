
var mix = {
  methods: {
    getProfile() {
      this.getData('/api/profile/').then(data => {
        this.fullName = data.fullName
        this.avatar = data.avatar
        this.phone = data.phone
        this.email = data.email
      }).catch(() => {})
    },
    changeProfile() {
      if (!this.fullName.trim().length || !this.email.trim().length) {
        alert('Required fields are missing')
        return
      }
      this.postData('/api/profile/', {
        fullName: this.fullName,
        phone: this.phone,
        email: this.email
      }).then(({ data }) => {
        this.fullName = data.fullName
        this.avatar = data.avatar
        this.phone = data.phone
        this.email = data.email
        alert('Saved')
      }).catch((error) => {
        alert(error.message)
      })
    },
    changePassword() {
      if (!this.passwordCurrent.trim().length || !this.password.trim().length || !this.passwordReply.trim().length || this.password !== this.passwordReply) {
        alert('Passwords are invalid')
        return
      }
      this.postData('/api/profile/password/', {
        currentPassword: this.passwordCurrent,
        password: this.password,
        passwordReply: this.passwordReply
      }).then(() => {
        alert('Password updated')
        this.passwordCurrent = ''
        this.password = ''
        this.passwordReply = ''
      }).catch((error) => {
        alert(error.message)
      })
    },
    setAvatar(event) {
      const file = event.target.files?.[0] ?? null
      if (!file) return
      const formData = new FormData()
      formData.append('avatar', file)
      this.postData('/api/profile/avatar/', formData, { 'Content-Type': 'multipart/form-data' })
        .then(({ data }) => {
          this.avatar = data
        }).catch((error) => {
          alert(error.message)
        })
    },
    clearAvatar() {
      this.avatar = null
    }
  },
  created() {
    this.getProfile()
  },
  data() {
    return {
      fullName: '',
      phone: '',
      email: '',
      avatar: null,
      password: '',
      passwordCurrent: '',
      passwordReply: ''
    }
  },
}
