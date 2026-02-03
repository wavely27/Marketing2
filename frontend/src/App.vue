<script setup lang="ts">
import { RouterView } from 'vue-router';
</script>

<template>
  <div id="app">
    <!-- Header -->
    <header class="app-header">
      <div class="header-content">
        <div class="brand">
          <h1>🎬 Marketing2</h1>
          <span class="tagline">AI Video Generator</span>
        </div>
        <div class="user-section">
          <span class="user-name">Admin</span>
          <div class="avatar">A</div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="app-main">
      <RouterView />
    </main>

    <!-- Footer -->
    <footer class="app-footer">
      <p>&copy; 2024 Marketing2 - Powered by AI</p>
    </footer>
  </div>
</template>

<style>
/* Global Dark Theme */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: #0f0f11;
  color: #ffffff;
  line-height: 1.6;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Header */
.app-header {
  background: #1e1e24;
  border-bottom: 1px solid #2a2a35;
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(10px);
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.brand {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.brand h1 {
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #00c3ff 0%, #7d3cff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.tagline {
  font-size: 0.9rem;
  color: #888;
  font-weight: 400;
}

.user-section {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-name {
  color: #fff;
  font-weight: 500;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #00c3ff 0%, #7d3cff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.2rem;
}

/* Main */
.app-main {
  flex: 1;
  width: 100%;
}

/* Footer */
.app-footer {
  background: #1e1e24;
  border-top: 1px solid #2a2a35;
  padding: 2rem;
  text-align: center;
  color: #888;
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #0f0f11;
}

::-webkit-scrollbar-thumb {
  background: #2a2a35;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #3a3a45;
}
</style>
