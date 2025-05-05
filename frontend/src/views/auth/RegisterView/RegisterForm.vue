<template>
  <div class="register-container">
    <form class="register-form" @submit.prevent="handleRegister">
      <h1>Cocoa Pod Disease Classification</h1>

      <div class="form-group">
        <label for="first-name">First Name</label>
        <input
          type="text"
          id="first-name"
          v-model="firstName"
          class="form-input"
          placeholder="Enter first name"
          required
        />
      </div>

      <div class="form-group">
        <label for="last-name">Last Name</label>
        <input
          type="text"
          id="last-name"
          v-model="lastName"
          class="form-input"
          placeholder="Enter last name"
          required
        />
      </div>

      <div class="form-group">
        <label for="email">Email</label>
        <input
          type="email"
          id="email"
          v-model="email"
          class="form-input"
          placeholder="Enter email"
          required
        />
      </div>

      <div class="form-group">
        <label for="password">Password</label>
        <input
          type="password"
          id="password"
          v-model="password"
          class="form-input"
          placeholder="Enter password"
          required
        />
      </div>

      <div class="form-group">
        <label for="confirm-password">Confirm Password</label>
        <input
          type="password"
          id="confirm-password"
          v-model="confirmPassword"
          class="form-input"
          placeholder="Confirm password"
          required
        />
      </div>

      <div class="form-group">
        <button type="submit" class="register-button">Register</button>
      </div>

      <!-- Display error or success messages -->
      <p v-if="error" class="error-message">{{ error }}</p>
      <p v-if="successMessage" class="success-message">{{ successMessage }}</p>

      <p class="login-link">
        Already have an account? <router-link to="/login">Login here</router-link>
      </p>
    </form>
  </div>
</template>

<script>
import { supabase } from '@/utils/supabase'

export default {
  data() {
    return {
      firstName: '',
      lastName: '',
      email: '',
      password: '',
      confirmPassword: '',
      error: null,
      successMessage: null,
    }
  },
  methods: {
    async handleRegister() {
      const { email, password, confirmPassword, firstName, lastName } = this

      // Reset previous messages
      this.error = ''
      this.successMessage = ''

      if (password !== confirmPassword) {
        this.error = 'Passwords do not match.'
        return
      }

      try {
        const { data, error: registerError } = await supabase.auth.signUp({
          email,
          password,
          options: {
            data: {
              first_name: firstName,
              last_name: lastName,
            },
          },
        })

        if (registerError) {
          this.error = registerError.message
          return
        }

        this.successMessage = 'Registration successful! Logging you in...'

        // Delay and redirect to login
        setTimeout(() => {
          this.$router.push('/login')

          // Reset form
          this.firstName = ''
          this.lastName = ''
          this.email = ''
          this.password = ''
          this.confirmPassword = ''
          this.successMessage = ''
          this.error = ''
        }, 2000)
      } catch (err) {
        this.error = err.message
      }
    },
  },
}
</script>

<style src="./RegisterView.css"></style>
