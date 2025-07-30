<script>
import axios from 'axios'

export default {
  name: 'App',
  data() {
    return {
      token: null,
      userRole: null,
      userData: {},
      currentView: 'userLogin', // Controls which view to show
      
      // Forms
      loginForm: { email: '', password: '' },
      signupForm: { email: '', password: '', fullname: '', address: '', pincode: '' },
      adminForm: { email: '', password: '' },
      adminSignupForm: { email: '', password: '', fullname: '', address: '', pincode: '' },
      profileForm: { fullname: '', address: '', pincode: '' },
      lotForm: { name: '', address: '', pincode: '', price: '', spots: '' },
      editLotForm: { name: '', address: '', pincode: '', price: '', spots: '' },
      editUserForm: { fullname: '', address: '', pincode: '' },
      bookingForm: { vehicle_number: '', duration: 1 },
      paymentForm: { method: '', amount: 0 },
      searchForm: { location: '', pincode: '' },
      adminSearchForm: { 
        searchQuery: '', 
        searchType: 'all',
        filterType: 'id' // New field for filter type
      },
      
      // Data arrays
      lots: [],
      reservations: [],
      adminLots: [],
      users: [],
      searchResults: { users: [], lots: [] },
      
      // Modals
      showBookingModal: false,
      showPaymentModal: false,
      showEditLotModal: false,
      showEditUserModal: false,
      selectedLotId: null,
      selectedReservationId: null,
      selectedLotForEdit: null,
      selectedUserForEdit: null,
      selectedLot: null, // Added to store selected lot for booking
      createUserForm: { email: '', password: '', fullname: '', address: '', pincode: '' },
      showCreateUserModal: false,
      paymentQRCode: null,
      paymentDetails: null,
      
      // Summary data
      userSummary: { booking_count: 0, total_spent: 0, total_time: 0, payment_count: 0 },
      adminSummary: { total_users: 0, total_revenue: 0, total_bookings: 0, total_payments: 0 }
    }
  },
  
  mounted() {
    // Check if user is already logged in
    const savedToken = localStorage.getItem('token')
    if (savedToken) {
      this.token = savedToken
      this.decodeToken()
      this.loadData()
    }
  },
  
  watch: {
    // Watch for changes in search type and adjust filter type accordingly
    'adminSearchForm.searchType'(newType) {
      if (newType === 'lots' && this.adminSearchForm.filterType === 'email') {
        this.adminSearchForm.filterType = 'id' // Reset to ID if email is selected for lots
      }
    }
  },
  
  methods: {
    // Navigation
    setView(view) {
      this.currentView = view
    },
    
    // User registration
    async register() {
      try {
        const response = await axios.post('/api/user/register', this.signupForm)
        alert('Registration successful! Please login.')
        this.currentView = 'userLogin'
        this.signupForm = { email: '', password: '', fullname: '', address: '', pincode: '' }
      } catch (error) {
        alert('Registration failed: ' + error.response?.data?.error || error.message)
      }
    },
    
    // User login
    async userLogin() {
      try {
        const response = await axios.post('/api/user/login', this.loginForm)
        this.token = response.data.token
        this.userRole = 'user'
        this.userData = response.data.user
        localStorage.setItem('token', this.token)
        this.currentView = 'userDashboard'
        this.loadData()
      } catch (error) {
        alert('Login failed: ' + error.response?.data?.error || error.message)
      }
    },
    
    // Admin registration
    async adminRegister() {
      try {
        const response = await axios.post('/api/admin/register', this.adminSignupForm)
        alert('Admin registration successful! Please login.')
        this.currentView = 'adminLogin'
        this.adminSignupForm = { email: '', password: '', fullname: '', address: '', pincode: '' }
      } catch (error) {
        alert('Admin registration failed: ' + error.response?.data?.error || error.message)
      }
    },
    
    // Admin login
    async adminLogin() {
      try {
        const response = await axios.post('/api/admin/login', this.adminForm)
        this.token = response.data.token
        this.userRole = 'admin'
        this.userData = response.data.admin
        localStorage.setItem('token', this.token)
        this.currentView = 'adminDashboard'
        this.loadData()
      } catch (error) {
        alert('Admin login failed: ' + error.response?.data?.error || error.message)
      }
    },
    
    // Logout
    logout() {
      this.token = null
      this.userRole = null
      this.userData = {}
      localStorage.removeItem('token')
      this.currentView = 'userLogin'
      this.lots = []
      this.reservations = []
      this.adminLots = []
      this.users = []
      this.searchResults = { users: [], lots: [] }
    },
    
    // Decode JWT token
    decodeToken() {
      try {
        const payload = JSON.parse(atob(this.token.split('.')[1]))
        this.userRole = payload.role
      } catch (error) {
        console.error('Error decoding token:', error)
        this.logout()
      }
    },
    
    // Load data based on user role
    async loadData() {
      if (this.userRole === 'user') {
        await this.loadUserData()
        await this.loadUserProfile()
        await this.loadUserSummary() // Load user summary for user
      } else if (this.userRole === 'admin') {
        await this.loadAdminData()
      }
    },
    
    // Load user data
    async loadUserData() {
      try {
        const [lotsResponse, reservationsResponse] = await Promise.all([
          axios.get('/api/user/lots', { headers: { Authorization: `Bearer ${this.token}` } }),
          axios.get('/api/user/reservations', { headers: { Authorization: `Bearer ${this.token}` } })
        ])
        this.lots = lotsResponse.data
        this.reservations = reservationsResponse.data
      } catch (error) {
        console.error('Failed to load user data:', error)
      }
    },
    
    // Load user profile data
    async loadUserProfile() {
      try {
        const response = await axios.get('/api/user/profile', { headers: { Authorization: `Bearer ${this.token}` } })
        this.profileForm = {
          fullname: response.data.fullname,
          address: response.data.address,
          pincode: response.data.pincode
        }
      } catch (error) {
        console.error('Failed to load user profile:', error)
      }
    },
    
    // Update user profile
    async updateProfile() {
      try {
        await axios.put('/api/user/profile', this.profileForm, { headers: { Authorization: `Bearer ${this.token}` } })
        alert('Profile updated successfully!')
        this.currentView = 'userDashboard'
        // Reload user data
        const response = await axios.get('/api/user/profile', { headers: { Authorization: `Bearer ${this.token}` } })
        this.userData = response.data
      } catch (error) {
        alert('Failed to update profile: ' + error.response?.data?.error || error.message)
      }
    },
    
    // Load admin data
    async loadAdminData() {
      try {
        const [lotsResponse, usersResponse, summaryResponse] = await Promise.all([
          axios.get('/api/admin/lots', { headers: { Authorization: `Bearer ${this.token}` } }),
          axios.get('/api/users', { headers: { Authorization: `Bearer ${this.token}` } }),
          axios.get('/api/admin/summary', { headers: { Authorization: `Bearer ${this.token}` } })
        ])
        this.adminLots = lotsResponse.data
        this.users = usersResponse.data
        this.adminSummary = summaryResponse.data
      } catch (error) {
        console.error('Error loading admin data:', error)
      }
    },
    
    // Search parking lots
    async searchLots() {
      try {
        const response = await axios.post('/api/search_slots', this.searchForm, { headers: { Authorization: `Bearer ${this.token}` } })
        this.lots = response.data.results
        if (this.lots.length === 0) {
          alert('No parking lots found matching your search criteria.')
        }
      } catch (error) {
        alert('Search failed: ' + error.response?.data?.error || error.message)
      }
    },
    
    // Clear search
    clearSearch() {
      this.searchForm = { location: '', pincode: '' }
      this.loadUserData()
    },
    
    // Admin search
    async adminSearch() {
      try {
        const response = await axios.post('/api/admin/search', {
          search_query: this.adminSearchForm.searchQuery,
          search_type: this.adminSearchForm.searchType,
          filter_type: this.adminSearchForm.filterType
        }, { headers: { Authorization: `Bearer ${this.token}` } })
        
        this.searchResults = {
          users: response.data.users || [],
          lots: response.data.lots || []
        }
      } catch (error) {
        alert('Search failed: ' + error.response?.data?.error || error.message)
      }
    },
    
    // Clear admin search
    clearAdminSearch() {
      this.adminSearchForm = { searchQuery: '', searchType: 'all', filterType: 'id' }
      this.searchResults = { users: [], lots: [] }
    },
    
    // Get search placeholder based on filter type
    getSearchPlaceholder() {
      const filterType = this.adminSearchForm.filterType
      const searchType = this.adminSearchForm.searchType
      
      if (searchType === 'users') {
        switch (filterType) {
          case 'id': return 'Enter user ID (e.g., 1, 2, 3...)'
          case 'name': return 'Enter user name (e.g., John Doe)'
          case 'email': return 'Enter email (e.g., john@example.com)'
          case 'pincode': return 'Enter pincode (e.g., 123456)'
          case 'address': return 'Enter address'
          default: return 'Enter search term...'
        }
      } else if (searchType === 'lots') {
        switch (filterType) {
          case 'id': return 'Enter lot ID (e.g., 1, 2, 3...)'
          case 'name': return 'Enter lot name (e.g., Central Parking)'
          case 'email': return 'Not applicable for lots'
          case 'pincode': return 'Enter pincode (e.g., 123456)'
          case 'address': return 'Enter address'
          default: return 'Enter search term...'
        }
      } else {
        switch (filterType) {
          case 'id': return 'Enter ID (user or lot)'
          case 'name': return 'Enter name (user or lot)'
          case 'email': return 'Enter email (users only)'
          case 'pincode': return 'Enter pincode'
          case 'address': return 'Enter address'
          default: return 'Enter search term...'
        }
      }
    },
    
    // Get search hint based on filter type
    getSearchHint() {
      const filterType = this.adminSearchForm.filterType
      const searchType = this.adminSearchForm.searchType
      
      if (searchType === 'users') {
        switch (filterType) {
          case 'id': return 'Search users by their ID number'
          case 'name': return 'Search users by their full name'
          case 'email': return 'Search users by their email address'
          case 'pincode': return 'Search users by their pincode'
          case 'address': return 'Search users by their address'
          default: return 'Search users by any field'
        }
      } else if (searchType === 'lots') {
        switch (filterType) {
          case 'id': return 'Search parking lots by their ID number'
          case 'name': return 'Search parking lots by their name'
          case 'email': return 'Email search not available for parking lots'
          case 'pincode': return 'Search parking lots by pincode'
          case 'address': return 'Search parking lots by address'
          default: return 'Search parking lots by any field'
        }
      } else {
        switch (filterType) {
          case 'id': return 'Search users and lots by ID'
          case 'name': return 'Search users by name and lots by name'
          case 'email': return 'Search users by email (lots not applicable)'
          case 'pincode': return 'Search users and lots by pincode'
          case 'address': return 'Search users and lots by address'
          default: return 'Search across all fields'
        }
      }
    },
    
    // Book parking spot
    bookSpot(lotId) {
      this.selectedLotId = lotId
      this.selectedLot = this.lots.find(lot => lot.id === lotId)
      this.showBookingModal = true
    },
    
    // View spots in a lot
    viewSpots(lotId) {
      // Implementation for viewing spots
      alert('View spots functionality - lot ID: ' + lotId)
    },
    
    // Confirm booking
    async confirmBooking() {
      try {
        const response = await axios.post('/api/user/book', {
          lot_id: this.selectedLotId,
          vehicle_number: this.bookingForm.vehicle_number,
          duration: this.bookingForm.duration
        }, { headers: { Authorization: `Bearer ${this.token}` } })
        
        alert('Spot booked successfully!')
        this.showBookingModal = false
        this.bookingForm = { vehicle_number: '', duration: 1 }
        this.loadUserData()
      } catch (error) {
        alert('Booking failed: ' + error.response?.data?.error || error.message)
      }
    },
    
    // Release parking spot
    async releaseSpot(reservationId) {
      try {
        const response = await axios.post('/api/user/release', { reservation_id: reservationId }, { headers: { Authorization: `Bearer ${this.token}` } })
        alert(`Spot released successfully! Cost: ₹${response.data.cost.toFixed(2)}`)
        this.loadUserData()
      } catch (error) {
        alert('Failed to release spot: ' + error.response?.data?.error || error.message)
      }
    },
    
    // Make payment
    makePayment(reservationId) {
      this.selectedReservationId = reservationId
      this.showPaymentModal = true
      this.loadPaymentQR(reservationId)
    },

    // Load payment QR code
    async loadPaymentQR(reservationId) {
      try {
        const response = await axios.get(`/api/user/payment/qr/${reservationId}`, 
          { headers: { Authorization: `Bearer ${this.token}` } })
        
        this.paymentQRCode = response.data.qr_code
        this.paymentDetails = response.data.payment_data
        
        // Show warning if QR code generation failed
        if (response.data.error) {
          console.warn('QR code generation failed:', response.data.error)
        }
      } catch (error) {
        alert('Failed to load payment QR: ' + error.response?.data?.error || error.message)
        this.showPaymentModal = false
      }
    },
    
    // Confirm payment
    async confirmPayment() {
      try {
        const response = await axios.post('/api/user/payment', {
          reservation_id: this.selectedReservationId,
          method: this.paymentForm.method
        }, { headers: { Authorization: `Bearer ${this.token}` } })
        
        alert(`Payment successful! Amount: ₹${response.data.amount.toFixed(2)}`)
        this.showPaymentModal = false
        this.paymentForm = { method: '', amount: 0 }
        this.paymentQRCode = null
        this.paymentDetails = null
        this.loadUserData()
      } catch (error) {
        alert('Payment failed: ' + error.response?.data?.error || error.message)
      }
    },
    
    // Download bill
    async downloadBill(reservationId) {
      try {
        // First get the payment for this reservation
        const reservation = this.reservations.find(r => r.id === reservationId)
        if (!reservation || !reservation.payment_id) {
          alert('No payment found for this reservation. Please make payment first.')
          return
        }
        
        // Download the bill
        const response = await axios.get(`/api/user/download-bill/${reservation.payment_id}`, {
          headers: { Authorization: `Bearer ${this.token}` },
          responseType: 'blob'
        })
        
        // Create download link
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `bill_${reservation.payment_id}.txt`)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
        
        alert('Bill downloaded successfully!')
      } catch (error) {
        alert('Failed to download bill: ' + error.response?.data?.error || error.message)
      }
    },
    
    // Export CSV
    async exportCSV() {
      try {
        const response = await axios.get('/api/user/export-csv', { headers: { Authorization: `Bearer ${this.token}` } })
        const csvContent = response.data.csv_content
        
        // Create download link
        const blob = new Blob([csvContent], { type: 'text/csv' })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', 'parking_history.csv')
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
        
        alert('CSV exported successfully!')
      } catch (error) {
        alert('Failed to export CSV: ' + error.response?.data?.error || error.message)
      }
    },
    
    // Create parking lot (admin)
    async createLot() {
      try {
        await axios.post('/api/admin/lots', this.lotForm, { headers: { Authorization: `Bearer ${this.token}` } })
        alert('Parking lot created successfully!')
        this.lotForm = { name: '', address: '', pincode: '', price: '', spots: '' }
        this.loadAdminData()
      } catch (error) {
        alert('Failed to create lot: ' + error.response?.data?.error || error.message)
      }
    },
    
    // Delete parking lot (admin)
    async deleteLot(lotId) {
      if (confirm('Are you sure you want to delete this parking lot?')) {
        try {
          await axios.delete(`/api/admin/lots/${lotId}`, { headers: { Authorization: `Bearer ${this.token}` } })
          alert('Parking lot deleted successfully!')
          this.loadAdminData()
        } catch (error) {
          alert('Failed to delete lot: ' + error.response?.data?.error || error.message)
        }
      }
    },
    
    // Edit parking lot (admin)
    editLot(lotId) {
      const lot = this.adminLots.find(l => l.id === lotId)
      if (lot) {
        this.selectedLotForEdit = lot
        this.editLotForm = {
          name: lot.prime_location_name,
          address: lot.address,
          pincode: lot.pincode,
          price: lot.price,
          spots: lot.number_of_spots
        }
        this.showEditLotModal = true
      }
    },
    
    // Update parking lot (admin)
    async updateLot() {
      try {
        await axios.put(`/api/admin/lots/${this.selectedLotForEdit.id}`, this.editLotForm, {
          headers: { Authorization: `Bearer ${this.token}` }
        })
        alert('Lot updated successfully!')
        this.showEditLotModal = false
        this.loadAdminData()
      } catch (error) {
        alert('Failed to update lot: ' + error.response?.data?.error || error.message)
      }
    },
    
    // Edit user (admin)
    editUser(userId) {
      const user = this.users.find(u => u.id === userId)
      if (user) {
        this.selectedUserForEdit = user
        this.editUserForm = {
          fullname: user.fullname,
          address: user.address,
          pincode: user.pincode
        }
        this.showEditUserModal = true
      }
    },
    
    // Update user (admin)
    async updateUser() {
      try {
        await axios.put(`/api/admin/users/${this.selectedUserForEdit.id}`, this.editUserForm, {
          headers: { Authorization: `Bearer ${this.token}` }
        })
        alert('User updated successfully!')
        this.showEditUserModal = false
        this.loadAdminData()
      } catch (error) {
        alert('Failed to update user: ' + error.response?.data?.error || error.message)
      }
    },
    
    // Delete user (admin)
    async deleteUser(userId) {
      if (confirm('Are you sure you want to delete this user?')) {
        try {
          await axios.delete(`/api/admin/users/${userId}`, { headers: { Authorization: `Bearer ${this.token}` } })
          alert('User deleted successfully!')
          this.loadAdminData()
        } catch (error) {
          alert('Failed to delete user: ' + error.response?.data?.error || error.message)
        }
      }
    },

    // Create user (admin)
    async createUser() {
      try {
        await axios.post('/api/admin/users', this.createUserForm, { headers: { Authorization: `Bearer ${this.token}` } })
        alert('User created successfully!')
        this.showCreateUserModal = false
        this.createUserForm = { email: '', password: '', fullname: '', address: '', pincode: '' }
        this.loadAdminData()
      } catch (error) {
        alert('Failed to create user: ' + error.response?.data?.error || error.message)
      }
    },

    // Load user summary
    async loadUserSummary() {
      try {
        const response = await axios.get('/api/user/summary', { headers: { Authorization: `Bearer ${this.token}` } })
        this.userSummary = response.data
      } catch (error) {
        console.error('Failed to load user summary:', error)
      }
    }
  }
}
</script>

<template>
  <div id="app">
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
      <div class="container">
        <a class="navbar-brand" href="#">Parking System</a>
        <div class="navbar-nav ms-auto">
          <button v-if="!token" @click="currentView = 'userLogin'" class="btn btn-outline-light me-2">User Login</button>
          <button v-if="!token" @click="currentView = 'userSignup'" class="btn btn-outline-light me-2">User Signup</button>
          <button v-if="!token" @click="currentView = 'adminLogin'" class="btn btn-warning me-2">Admin Login</button>
          <button v-if="!token" @click="currentView = 'adminSignup'" class="btn btn-warning me-2">Admin Signup</button>
          <button v-if="token" @click="logout" class="btn btn-danger">Logout</button>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <div class="container mt-4">
      <!-- User Signup Form -->
      <div v-if="currentView === 'userSignup'" class="row justify-content-center">
        <div class="col-md-6">
          <div class="card">
            <div class="card-header">
              <h4>User Registration</h4>
            </div>
            <div class="card-body">
              <form @submit.prevent="register">
                <div class="mb-3">
                  <label class="form-label">Email</label>
                  <input v-model="signupForm.email" type="email" class="form-control" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">Password</label>
                  <input v-model="signupForm.password" type="password" class="form-control" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">Full Name</label>
                  <input v-model="signupForm.fullname" type="text" class="form-control" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">Address</label>
                  <input v-model="signupForm.address" type="text" class="form-control" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">Pincode</label>
                  <input v-model="signupForm.pincode" type="text" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-primary">Register</button>
                <button type="button" @click="currentView = 'userLogin'" class="btn btn-secondary ms-2">Back to Login</button>
              </form>
            </div>
          </div>
        </div>
      </div>

      <!-- User Login Form -->
      <div v-if="currentView === 'userLogin'" class="row justify-content-center">
        <div class="col-md-6">
          <div class="card">
            <div class="card-header">
              <h4>User Login</h4>
            </div>
            <div class="card-body">
              <form @submit.prevent="userLogin">
                <div class="mb-3">
                  <label class="form-label">Email</label>
                  <input v-model="loginForm.email" type="email" class="form-control" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">Password</label>
                  <input v-model="loginForm.password" type="password" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-primary">Login</button>
                <button type="button" @click="currentView = 'userSignup'" class="btn btn-secondary ms-2">Register</button>
              </form>
            </div>
          </div>
        </div>
      </div>

      <!-- Admin Login Form -->
      <div v-if="currentView === 'adminLogin'" class="row justify-content-center">
        <div class="col-md-6">
          <div class="card">
            <div class="card-header">
              <h4>Admin Login</h4>
            </div>
            <div class="card-body">
              <form @submit.prevent="adminLogin">
                <div class="mb-3">
                  <label class="form-label">Email</label>
                  <input v-model="adminForm.email" type="email" class="form-control" placeholder="admin@admin.com" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">Password</label>
                  <input v-model="adminForm.password" type="password" class="form-control" placeholder="admin123" required>
                </div>
                <button type="submit" class="btn btn-warning">Admin Login</button>
                <button type="button" @click="currentView = 'adminSignup'" class="btn btn-secondary ms-2">Admin Register</button>
                <button type="button" @click="currentView = 'userLogin'" class="btn btn-secondary ms-2">Back to User Login</button>
                <div class="mt-2">
                  <small class="text-muted">Default: admin@admin.com / admin123</small>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>

      <!-- Admin Signup Form -->
      <div v-if="currentView === 'adminSignup'" class="row justify-content-center">
        <div class="col-md-6">
          <div class="card">
            <div class="card-header">
              <h4>Admin Registration</h4>
            </div>
            <div class="card-body">
              <form @submit.prevent="adminRegister">
                <div class="mb-3">
                  <label class="form-label">Email</label>
                  <input v-model="adminSignupForm.email" type="email" class="form-control" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">Password</label>
                  <input v-model="adminSignupForm.password" type="password" class="form-control" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">Full Name</label>
                  <input v-model="adminSignupForm.fullname" type="text" class="form-control" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">Address</label>
                  <input v-model="adminSignupForm.address" type="text" class="form-control" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">Pincode</label>
                  <input v-model="adminSignupForm.pincode" type="text" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-warning">Register Admin</button>
                <button type="button" @click="currentView = 'adminLogin'" class="btn btn-secondary ms-2">Back to Admin Login</button>
              </form>
            </div>
          </div>
        </div>
      </div>

      <!-- User Dashboard -->
      <div v-if="token && userRole === 'user' && currentView === 'userDashboard'" class="row">
        <div class="col-md-12">
          <div class="d-flex justify-content-between align-items-center mb-4">
            <h2>Welcome, {{ userData.fullname }}!</h2>
            <div>
              <button @click="currentView = 'userProfile'" class="btn btn-info me-2">Edit Profile</button>
              <button @click="currentView = 'userSummary'" class="btn btn-success">View Summary</button>
            </div>
          </div>
          
          <!-- Search Parking Lots -->
          <div class="card mb-4">
            <div class="card-header">
              <h5>Search Parking Lots</h5>
            </div>
            <div class="card-body">
              <div class="row">
                <div class="col-md-4">
                  <input v-model="searchForm.location" type="text" class="form-control" placeholder="Search by location...">
                </div>
                <div class="col-md-4">
                  <input v-model="searchForm.pincode" type="text" class="form-control" placeholder="Search by pincode...">
                </div>
                <div class="col-md-4">
                  <button @click="searchLots" class="btn btn-primary">Search</button>
                  <button @click="clearSearch" class="btn btn-secondary ms-2">Clear</button>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Available Parking Lots -->
          <div class="card mb-4">
            <div class="card-header">
              <h5>Available Parking Lots</h5>
            </div>
            <div class="card-body">
              <div v-if="lots.length === 0" class="text-center">
                <p>No parking lots available</p>
              </div>
              <div v-else class="row">
                <div v-for="lot in lots" :key="lot.id" class="col-md-4 mb-3">
                  <div class="card">
                    <div class="card-body">
                      <h6>{{ lot.prime_location_name }}</h6>
                      <p><strong>Address:</strong> {{ lot.address }}</p>
                      <p><strong>Pincode:</strong> {{ lot.pincode }}</p>
                      <p><strong>Price:</strong> ₹{{ lot.price }}/hour</p>
                      <p><strong>Available Spots:</strong> {{ lot.number_of_spots }}</p>
                      <button @click="bookSpot(lot.id)" class="btn btn-primary btn-sm">Book Spot</button>
                      <button @click="viewSpots(lot.id)" class="btn btn-info btn-sm ms-2">View Spots</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- User Reservations -->
          <div class="card">
            <div class="card-header">
              <h5>My Reservations</h5>
            </div>
            <div class="card-body">
              <div v-if="reservations.length === 0" class="text-center">
                <p>No reservations found</p>
              </div>
              <div v-else>
                <div v-for="reservation in reservations" :key="reservation.id" class="border-bottom pb-2 mb-2">
                  <p><strong>Vehicle:</strong> {{ reservation.vehicle_number }}</p>
                  <p><strong>Parked:</strong> {{ reservation.parking_timestamp }}</p>
                  <p><strong>Status:</strong> 
                    <span :class="reservation.status === 'active' ? 'text-warning' : 'text-success'">
                      {{ reservation.status === 'active' ? 'Currently Parked' : 'Completed' }}
                    </span>
                  </p>
                  <p v-if="reservation.status === 'completed' && reservation.parking_cost">
                    <strong>Cost:</strong> ₹{{ reservation.parking_cost.toFixed(2) }}
                  </p>
                  <div class="btn-group">
                    <button v-if="reservation.status === 'active'" @click="releaseSpot(reservation.id)" class="btn btn-danger btn-sm">Release Spot</button>
                    <button v-if="reservation.status === 'completed' && !reservation.payment_id" @click="makePayment(reservation.id)" class="btn btn-success btn-sm">Make Payment</button>
                    <button v-if="reservation.payment_id" @click="downloadBill(reservation.id)" class="btn btn-info btn-sm">Download Bill</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- User Profile Edit -->
      <div v-if="token && userRole === 'user' && currentView === 'userProfile'" class="row justify-content-center">
        <div class="col-md-8">
          <div class="card">
            <div class="card-header">
              <h4>Edit Profile</h4>
            </div>
            <div class="card-body">
              <form @submit.prevent="updateProfile">
                <div class="mb-3">
                  <label class="form-label">Full Name</label>
                  <input v-model="profileForm.fullname" type="text" class="form-control" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">Address</label>
                  <input v-model="profileForm.address" type="text" class="form-control" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">Pincode</label>
                  <input v-model="profileForm.pincode" type="text" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-primary">Update Profile</button>
                <button type="button" @click="currentView = 'userDashboard'" class="btn btn-secondary ms-2">Back to Dashboard</button>
              </form>
            </div>
          </div>
        </div>
      </div>

      <!-- User Summary -->
      <div v-if="token && userRole === 'user' && currentView === 'userSummary'" class="row">
        <div class="col-md-12">
          <div class="card">
            <div class="card-header">
              <h4>User Summary</h4>
            </div>
            <div class="card-body">
              <div class="row">
                <div class="col-md-3">
                  <div class="card bg-primary text-white">
                    <div class="card-body text-center">
                      <h5>Total Bookings</h5>
                      <h3>{{ userSummary.user_booking_count }}</h3>
                    </div>
                  </div>
                </div>
                <div class="col-md-3">
                  <div class="card bg-success text-white">
                    <div class="card-body text-center">
                      <h5>Total Spent</h5>
                      <h3>₹{{ userSummary.user_total_spent }}</h3>
                    </div>
                  </div>
                </div>
                <div class="col-md-3">
                  <div class="card bg-info text-white">
                    <div class="card-body text-center">
                      <h5>Total Time</h5>
                      <h3>{{ userSummary.user_total_time }}h</h3>
                    </div>
                  </div>
                </div>
                <div class="col-md-3">
                  <div class="card bg-warning text-white">
                    <div class="card-body text-center">
                      <h5>Payments</h5>
                      <h3>{{ userSummary.user_payment_count }}</h3>
                    </div>
                  </div>
                </div>
              </div>
              <div class="mt-3">
                <button @click="exportCSV" class="btn btn-success">Export CSV</button>
                <button @click="currentView = 'userDashboard'" class="btn btn-secondary ms-2">Back to Dashboard</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Admin Dashboard -->
      <div v-if="token && userRole === 'admin' && currentView === 'adminDashboard'" class="row">
        <div class="col-md-12">
          <div class="d-flex justify-content-between align-items-center mb-4">
            <h2>Admin Dashboard</h2>
            <div>
              <button @click="currentView = 'adminUsers'" class="btn btn-info me-2">Manage Users</button>
              <button @click="currentView = 'adminSummary'" class="btn btn-success">View Summary</button>
              <button @click="currentView = 'adminSearch'" class="btn btn-warning">Search</button>
            </div>
          </div>
          
          <!-- Create Parking Lot -->
          <div class="card mb-4">
            <div class="card-header">
              <h5>Create New Parking Lot</h5>
            </div>
            <div class="card-body">
              <form @submit.prevent="createLot">
                <div class="row">
                  <div class="col-md-3">
                    <input v-model="lotForm.name" type="text" class="form-control" placeholder="Location Name" required>
                  </div>
                  <div class="col-md-3">
                    <input v-model="lotForm.address" type="text" class="form-control" placeholder="Address" required>
                  </div>
                  <div class="col-md-2">
                    <input v-model="lotForm.pincode" type="text" class="form-control" placeholder="Pincode" required>
                  </div>
                  <div class="col-md-2">
                    <input v-model="lotForm.price" type="number" class="form-control" placeholder="Price/Hour" required>
                  </div>
                  <div class="col-md-2">
                    <input v-model="lotForm.spots" type="number" class="form-control" placeholder="Number of Spots" required>
                  </div>
                </div>
                <button type="submit" class="btn btn-success mt-2">Create Lot</button>
              </form>
            </div>
          </div>

          <!-- All Parking Lots -->
          <div class="card">
            <div class="card-header">
              <h5>All Parking Lots</h5>
            </div>
            <div class="card-body">
              <div v-if="adminLots.length === 0" class="text-center">
                <p>No parking lots created yet</p>
              </div>
              <div v-else>
                <div v-for="lot in adminLots" :key="lot.id" class="border-bottom pb-2 mb-2">
                  <div class="row align-items-center">
                    <div class="col-md-8">
                      <h6>{{ lot.prime_location_name }}</h6>
                      <p class="mb-1"><strong>Address:</strong> {{ lot.address }}</p>
                      <p class="mb-1"><strong>Pincode:</strong> {{ lot.pincode }}</p>
                      <p class="mb-1"><strong>Price:</strong> ₹{{ lot.price }}/hour</p>
                      <p class="mb-0"><strong>Spots:</strong> {{ lot.number_of_spots }}</p>
                    </div>
                    <div class="col-md-4 text-end">
                      <button @click="editLot(lot.id)" class="btn btn-warning btn-sm me-2">Edit</button>
                      <button @click="deleteLot(lot.id)" class="btn btn-danger btn-sm">Delete</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Admin Users Management -->
      <div v-if="token && userRole === 'admin' && currentView === 'adminUsers'" class="row">
        <div class="col-md-12">
          <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
              <h4>Manage Users</h4>
              <button @click="showCreateUserModal = true" class="btn btn-success">Add New User</button>
            </div>
            <div class="card-body">
              <div v-if="users.length === 0" class="text-center">
                <p>No users found</p>
              </div>
              <div v-else>
                <div v-for="user in users" :key="user.id" class="border-bottom pb-2 mb-2">
                  <div class="row align-items-center">
                    <div class="col-md-8">
                      <h6>{{ user.fullname }}</h6>
                      <p class="mb-1"><strong>Email:</strong> {{ user.email }}</p>
                      <p class="mb-1"><strong>Address:</strong> {{ user.address }}</p>
                      <p class="mb-0"><strong>Pincode:</strong> {{ user.pincode }}</p>
                    </div>
                    <div class="col-md-4 text-end">
                      <button @click="editUser(user.id)" class="btn btn-warning btn-sm me-2">Edit</button>
                      <button @click="deleteUser(user.id)" class="btn btn-danger btn-sm">Delete</button>
                    </div>
                  </div>
                </div>
              </div>
              <button @click="currentView = 'adminDashboard'" class="btn btn-secondary mt-3">Back to Dashboard</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Admin Summary -->
      <div v-if="token && userRole === 'admin' && currentView === 'adminSummary'" class="row">
        <div class="col-md-12">
          <div class="card">
            <div class="card-header">
              <h4>Admin Summary</h4>
            </div>
            <div class="card-body">
              <div class="row">
                <div class="col-md-3">
                  <div class="card bg-primary text-white">
                    <div class="card-body text-center">
                      <h5>Total Users</h5>
                      <h3>{{ adminSummary.total_users }}</h3>
                    </div>
                  </div>
                </div>
                <div class="col-md-3">
                  <div class="card bg-success text-white">
                    <div class="card-body text-center">
                      <h5>Total Revenue</h5>
                      <h3>₹{{ adminSummary.total_revenue }}</h3>
                    </div>
                  </div>
                </div>
                <div class="col-md-3">
                  <div class="card bg-info text-white">
                    <div class="card-body text-center">
                      <h5>Total Bookings</h5>
                      <h3>{{ adminSummary.total_bookings }}</h3>
                    </div>
                  </div>
                </div>
                <div class="col-md-3">
                  <div class="card bg-warning text-white">
                    <div class="card-body text-center">
                      <h5>Total Payments</h5>
                      <h3>{{ adminSummary.total_payments }}</h3>
                    </div>
                  </div>
                </div>
              </div>
              <button @click="currentView = 'adminDashboard'" class="btn btn-secondary mt-3">Back to Dashboard</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Admin Search -->
      <div v-if="token && userRole === 'admin' && currentView === 'adminSearch'" class="row">
        <div class="col-md-12">
          <div class="card">
            <div class="card-header">
              <h4>Admin Search</h4>
            </div>
            <div class="card-body">
              <div class="row mb-3">
                <div class="col-md-3">
                  <label class="form-label">Search Type</label>
                  <select v-model="adminSearchForm.searchType" class="form-control">
                    <option value="all">All (Users & Lots)</option>
                    <option value="users">Users Only</option>
                    <option value="lots">Lots Only</option>
                  </select>
                </div>
                <div class="col-md-3">
                  <label class="form-label">Filter By</label>
                  <select v-model="adminSearchForm.filterType" class="form-control">
                    <option value="id">ID</option>
                    <option value="name">Name</option>
                    <option value="email" :disabled="adminSearchForm.searchType === 'lots'">Email</option>
                    <option value="pincode">Pincode</option>
                    <option value="address">Address</option>
                  </select>
                </div>
                <div class="col-md-4">
                  <label class="form-label">Search Input</label>
                  <input v-model="adminSearchForm.searchQuery" type="text" class="form-control" 
                         :placeholder="getSearchPlaceholder()">
                  <small class="form-text text-muted">
                    {{ getSearchHint() }}
                  </small>
                </div>
                <div class="col-md-2">
                  <label class="form-label">&nbsp;</label>
                  <div>
                    <button @click="adminSearch" class="btn btn-primary w-100">Search</button>
                  </div>
                </div>
              </div>
              
              <div class="row mb-3">
                <div class="col-md-12">
                  <button @click="clearAdminSearch" class="btn btn-secondary">Clear Search</button>
                  <button @click="adminSearch" class="btn btn-outline-primary ms-2">Show All</button>
                </div>
              </div>
              
              <!-- Search Results -->
              <div v-if="searchResults.users.length > 0 || searchResults.lots.length > 0">
                <h5>Search Results:</h5>
                
                <!-- Users Results -->
                <div v-if="searchResults.users.length > 0" class="mb-4">
                  <h6 class="text-primary">Users Found ({{ searchResults.users.length }})</h6>
                  <div v-for="user in searchResults.users" :key="user.id" class="border-bottom pb-2 mb-2">
                    <div class="row align-items-center">
                      <div class="col-md-8">
                        <h6>{{ user.fullname }}</h6>
                        <p class="mb-1"><strong>ID:</strong> {{ user.id }}</p>
                        <p class="mb-1"><strong>Email:</strong> {{ user.email }}</p>
                        <p class="mb-1"><strong>Address:</strong> {{ user.address }}</p>
                        <p class="mb-0"><strong>Pincode:</strong> {{ user.pincode }}</p>
                      </div>
                      <div class="col-md-4 text-end">
                        <button @click="editUser(user.id)" class="btn btn-warning btn-sm me-2">Edit</button>
                        <button @click="deleteUser(user.id)" class="btn btn-danger btn-sm">Delete</button>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- Lots Results -->
                <div v-if="searchResults.lots.length > 0">
                  <h6 class="text-success">Parking Lots Found ({{ searchResults.lots.length }})</h6>
                  <div v-for="lot in searchResults.lots" :key="lot.id" class="border-bottom pb-2 mb-2">
                    <div class="row align-items-center">
                      <div class="col-md-8">
                        <h6>{{ lot.prime_location_name }}</h6>
                        <p class="mb-1"><strong>ID:</strong> {{ lot.id }}</p>
                        <p class="mb-1"><strong>Address:</strong> {{ lot.address }}</p>
                        <p class="mb-1"><strong>Pincode:</strong> {{ lot.pincode }}</p>
                        <p class="mb-1"><strong>Price:</strong> ₹{{ lot.price }}/hour</p>
                        <p class="mb-0"><strong>Spots:</strong> {{ lot.number_of_spots }}</p>
                      </div>
                      <div class="col-md-4 text-end">
                        <button @click="editLot(lot.id)" class="btn btn-warning btn-sm me-2">Edit</button>
                        <button @click="deleteLot(lot.id)" class="btn btn-danger btn-sm">Delete</button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- No Results Message -->
              <div v-else-if="adminSearchForm.searchQuery && (searchResults.users.length === 0 && searchResults.lots.length === 0)" class="text-center mt-4">
                <p class="text-muted">No results found for "{{ adminSearchForm.searchQuery }}"</p>
              </div>
              
              <button @click="currentView = 'adminDashboard'" class="btn btn-secondary mt-3">Back to Dashboard</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Booking Modal -->
      <div v-if="showBookingModal" class="modal fade show" style="display: block;" tabindex="-1">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Book Parking Spot</h5>
              <button type="button" class="btn-close" @click="showBookingModal = false"></button>
            </div>
            <div class="modal-body">
              <form @submit.prevent="confirmBooking">
                <div class="mb-3">
                  <label class="form-label">Vehicle Number</label>
                  <input v-model="bookingForm.vehicle_number" type="text" class="form-control" placeholder="e.g., MH12AB1234" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">Duration (hours)</label>
                  <input v-model="bookingForm.duration" type="number" class="form-control" min="1" max="24" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">Expected Cost</label>
                  <input type="text" class="form-control" :value="selectedLot ? `₹${(bookingForm.duration * selectedLot.price).toFixed(2)}` : '₹0.00'" readonly>
                </div>
                <button type="submit" class="btn btn-primary">Confirm Booking</button>
                <button type="button" @click="showBookingModal = false" class="btn btn-secondary ms-2">Cancel</button>
              </form>
            </div>
          </div>
        </div>
      </div>

      <!-- Payment Modal -->
      <div v-if="showPaymentModal" class="modal fade show" style="display: block;" tabindex="-1">
        <div class="modal-dialog modal-lg">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Make Payment</h5>
              <button type="button" class="btn-close" @click="showPaymentModal = false"></button>
            </div>
            <div class="modal-body">
              <!-- Payment Details -->
              <div v-if="paymentDetails" class="row mb-4">
                <div class="col-md-6">
                  <h6 class="text-primary">Payment Details</h6>
                  <div class="card">
                    <div class="card-body">
                      <p><strong>Booking ID:</strong> {{ paymentDetails.booking_id }}</p>
                      <p><strong>Customer:</strong> {{ paymentDetails.user_name }}</p>
                      <p><strong>Vehicle:</strong> {{ paymentDetails.vehicle_number }}</p>
                      <p><strong>Location:</strong> {{ paymentDetails.location }}</p>
                      <p><strong>Duration:</strong> {{ paymentDetails.duration_hours }} hours</p>
                      <p><strong>Amount:</strong> ₹{{ paymentDetails.amount }}</p>
                    </div>
                  </div>
                </div>
                <div class="col-md-6">
                  <h6 class="text-success">QR Code Payment</h6>
                  <div class="text-center">
                    <img v-if="paymentQRCode" :src="paymentQRCode" alt="Payment QR Code" 
                         class="img-fluid border" style="max-width: 200px;">
                    <div v-else class="alert alert-warning">
                      <strong>QR Code Unavailable</strong><br>
                      <small>You can still make payment using other methods below.</small>
                    </div>
                    <p class="mt-2 text-muted small" v-if="paymentQRCode">
                      Scan this QR code with any UPI app to pay ₹{{ paymentDetails?.amount }}
                    </p>
                  </div>
                </div>
              </div>

              <!-- Payment Method Selection -->
              <div class="row">
                <div class="col-md-12">
                  <h6>Payment Method</h6>
                  <div class="mb-3">
                    <div class="form-check">
                      <input v-model="paymentForm.method" value="upi" type="radio" class="form-check-input" id="upi">
                      <label class="form-check-label" for="upi">UPI (QR Code)</label>
                    </div>
                    <div class="form-check">
                      <input v-model="paymentForm.method" value="card" type="radio" class="form-check-input" id="card">
                      <label class="form-check-label" for="card">Credit/Debit Card</label>
                    </div>
                    <div class="form-check">
                      <input v-model="paymentForm.method" value="cash" type="radio" class="form-check-input" id="cash">
                      <label class="form-check-label" for="cash">Cash</label>
                    </div>
                  </div>
                  
                  <div class="alert alert-info">
                    <strong>Note:</strong> Amount will be calculated automatically based on your parking duration.
                    <br>
                    <strong>Amount:</strong> ₹{{ paymentDetails?.amount || 'Calculating...' }}
                  </div>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button @click="confirmPayment" class="btn btn-primary">Confirm Payment</button>
              <button @click="showPaymentModal = false" class="btn btn-secondary">Cancel</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Edit Lot Modal -->
      <div v-if="showEditLotModal" class="modal fade show" style="display: block;" tabindex="-1">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Edit Parking Lot</h5>
              <button type="button" class="btn-close" @click="showEditLotModal = false"></button>
            </div>
            <div class="modal-body">
              <form @submit.prevent="updateLot">
                <div class="mb-3">
                  <label class="form-label">Lot Name</label>
                  <input v-model="editLotForm.name" type="text" class="form-control" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">Address</label>
                  <input v-model="editLotForm.address" type="text" class="form-control" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">Pincode</label>
                  <input v-model="editLotForm.pincode" type="text" class="form-control" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">Price per Hour</label>
                  <input v-model="editLotForm.price" type="number" class="form-control" step="0.01" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">Number of Spots</label>
                  <input v-model="editLotForm.spots" type="number" class="form-control" min="1" required>
                </div>
                <button type="submit" class="btn btn-primary">Update Lot</button>
                <button type="button" @click="showEditLotModal = false" class="btn btn-secondary ms-2">Cancel</button>
              </form>
            </div>
          </div>
        </div>
      </div>

      <!-- Edit User Modal -->
      <div v-if="showEditUserModal" class="modal fade show" style="display: block;" tabindex="-1">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Edit User</h5>
              <button type="button" class="btn-close" @click="showEditUserModal = false"></button>
            </div>
            <div class="modal-body">
              <form @submit.prevent="updateUser">
                <div class="mb-3">
                  <label class="form-label">Full Name</label>
                  <input v-model="editUserForm.fullname" type="text" class="form-control" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">Address</label>
                  <input v-model="editUserForm.address" type="text" class="form-control" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">Pincode</label>
                  <input v-model="editUserForm.pincode" type="text" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-primary">Update User</button>
                <button type="button" @click="showEditUserModal = false" class="btn btn-secondary ms-2">Cancel</button>
              </form>
            </div>
          </div>
        </div>
      </div>

      <!-- Create User Modal -->
      <div v-if="showCreateUserModal" class="modal fade show" style="display: block;" tabindex="-1">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Create New User</h5>
              <button type="button" class="btn-close" @click="showCreateUserModal = false"></button>
            </div>
            <div class="modal-body">
              <form @submit.prevent="createUser">
                <div class="mb-3">
                  <label class="form-label">Email</label>
                  <input v-model="createUserForm.email" type="email" class="form-control" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">Password</label>
                  <input v-model="createUserForm.password" type="password" class="form-control" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">Full Name</label>
                  <input v-model="createUserForm.fullname" type="text" class="form-control" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">Address</label>
                  <input v-model="createUserForm.address" type="text" class="form-control" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">Pincode</label>
                  <input v-model="createUserForm.pincode" type="text" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-primary">Create User</button>
                <button type="button" @click="showCreateUserModal = false" class="btn btn-secondary ms-2">Cancel</button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
#app {
  font-family: Arial, sans-serif;
}

.card {
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.btn {
  border-radius: 4px;
}

.modal {
  background-color: rgba(0,0,0,0.5);
}
</style>
