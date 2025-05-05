<!-- Import external CSS -->
<style src="./LoginView.css"></style>

<template>
  <div class="login-background">
    <div class="login-container">
      <form @submit.prevent="handleLogin">
        <h1>Cocoa Pod Disease Classification</h1>
        <!-- Email -->
        <div class="form-group">
          <label for="email">Email</label>
          <input type="email" id="email" v-model="email" placeholder="Enter your email" required />
        </div>

        <!-- Password -->
        <div class="form-group">
          <label for="password">Password</label>
          <input
            type="password"
            id="password"
            v-model="password"
            placeholder="Enter your password"
            required
          />
        </div>

        <!-- Role -->
        <div class="form-group">
          <label for="role">Role</label>
          <input
            type="text"
            id="role"
            v-model="role"
            placeholder="Student/Researcher/Farmer"
            required
          />
        </div>

        <div class="form-group">
          <button type="submit">Login</button>
        </div>
        <p class="register-link">
          Don't have an account? <router-link to="/register">Create an Account</router-link>
        </p>
      </form>
    </div>
  </div>
</template>

<script>
import { supabase } from '@/utils/supabase'

export default {
  name: 'LoginView',
  data() {
    return {
      email: '',
      password: '',
      role: '',
    }
  },
  methods: {
    async handleLogin() {
      const { data, error } = await supabase.auth.signInWithPassword({
        email: this.email,
        password: this.password,
      })

      if (error) {
        alert('Login failed: ' + error.message)
      } else {
        console.log('Login success:', data)
        this.$router.push('/dashboard') //  redirect here
      }
    },
  },
}
</script>
