<template>
  <div class="login-container">
    <div class="login-card">
      <!-- Header -->
      <div class="login-header">
        <h1 class="login-title">TenderLENZZ</h1>
        <p class="login-subtitle">AI Tender Compliance Copilot</p>
      </div>

      <!-- Error Message -->
      <div v-if="authStore.authError" class="alert alert-error">
        <span class="alert-icon">⚠️</span>
        <span>{{ authStore.authError }}</span>
      </div>

      <!-- Login Form -->
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username" class="form-label">Username</label>
          <input
            id="username"
            v-model="username"
            type="text"
            class="form-input"
            placeholder="Enter username"
            required
            autocomplete="username"
            :disabled="authStore.isAuthenticating"
          />
        </div>

        <div class="form-group">
          <label for="password" class="form-label">Password</label>
          <input
            id="password"
            v-model="password"
            type="password"
            class="form-input"
            placeholder="Enter password"
            required
            autocomplete="current-password"
            :disabled="authStore.isAuthenticating"
          />
        </div>

        <button
          type="submit"
          class="btn btn-primary btn-block"
          :disabled="authStore.isAuthenticating || !username || !password"
        >
          {{ authStore.isAuthenticating ? '⏳ Logging in...' : '🔐 Login' }}
        </button>
      </form>

      <!-- Demo Credentials -->
      <div class="demo-info">
        <p class="demo-title">Demo Credentials:</p>
        <div class="demo-credentials">
          <div class="demo-user">
            <strong>Officer:</strong> officer1 / demo123
          </div>
          <div class="demo-user">
            <strong>Bidder:</strong> bidder1 / demo123
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')

const handleLogin = async () => {
  const success = await authStore.login(username.value, password.value)

  if (success) {
    // Redirect to dashboard after successful login
    router.push('/')
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 1rem;
}

.login-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  padding: 2.5rem;
  width: 100%;
  max-width: 420px;
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.login-title {
  font-size: 2rem;
  font-weight: 800;
  color: #1e293b;
  margin-bottom: 0.5rem;
}

.login-subtitle {
  font-size: 0.95rem;
  color: #64748b;
}

.alert {
  padding: 0.75rem 1rem;
  border-radius: 6px;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.alert-error {
  background: #fee;
  color: #991b1b;
  border: 1px solid #fcc;
}

.alert-icon {
  font-size: 1.2rem;
}

.login-form {
  margin-bottom: 2rem;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-label {
  display: block;
  font-size: 0.85rem;
  font-weight: 600;
  color: #334155;
  margin-bottom: 0.5rem;
}

.form-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.95rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-input:disabled {
  background: #f1f5f9;
  cursor: not-allowed;
}

.btn {
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: background-color 0.2s, transform 0.1s;
}

.btn:active {
  transform: translateY(1px);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #5568d3;
}

.btn-block {
  width: 100%;
}

.demo-info {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 1rem;
}

.demo-title {
  font-size: 0.75rem;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}

.demo-credentials {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.demo-user {
  font-size: 0.85rem;
  color: #475569;
  font-family: monospace;
}
</style>
