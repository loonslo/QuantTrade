# Frontend Development Workflow

## Overview

This document outlines the development workflow for the QuantTradeSys frontend application, including setup, development practices, testing, and deployment procedures.

## Development Environment Setup

### Prerequisites

1. **Node.js**: Version 18+ (recommended: 20.19.0 or 22.12.0+)
2. **Package Manager**: npm 8+ or yarn 1.22+
3. **Code Editor**: VS Code with recommended extensions
4. **Git**: For version control

### Recommended VS Code Extensions

```json
{
  "recommendations": [
    "vue.volar",
    "vue.vscode-typescript-vue-plugin",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "bradlc.vscode-tailwindcss",
    "ms-vscode.vscode-json"
  ]
}
```

### Initial Setup

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd QuantTradeSys
   ```

2. **Navigate to Frontend**
   ```bash
   cd frontend/crypto-report
   ```

3. **Install Dependencies**
   ```bash
   npm install
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your configuration
   ```

5. **Start Development Server**
   ```bash
   npm run dev
   # Or use the Python script
   python ../../scripts/dev/start_frontend.py
   ```

## Development Workflow

### 1. Feature Development Process

#### Branch Strategy
```bash
# Create feature branch
git checkout -b feature/market-analysis-component

# Work on feature
# ... make changes ...

# Commit changes
git add .
git commit -m "feat: add market analysis component with real-time updates"

# Push to remote
git push origin feature/market-analysis-component

# Create pull request
```

#### Commit Message Convention
Follow conventional commits format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

### 2. Code Organization

#### Component Structure
```vue
<template>
  <!-- Template content -->
</template>

<script>
// Component logic
export default {
  name: 'ComponentName',
  props: {
    // Props definition
  },
  data() {
    return {
      // Component state
    }
  },
  computed: {
    // Computed properties
  },
  methods: {
    // Component methods
  },
  mounted() {
    // Lifecycle hooks
  }
}
</script>

<style scoped>
/* Component styles */
</style>
```

#### File Naming Conventions
- **Components**: PascalCase (e.g., `MarketOverview.vue`)
- **Views**: PascalCase with "View" suffix (e.g., `HomeView.vue`)
- **Stores**: camelCase (e.g., `cryptoStore.js`)
- **Services**: camelCase (e.g., `apiService.js`)
- **Utils**: camelCase (e.g., `formatUtils.js`)

### 3. State Management

#### Pinia Store Pattern
```javascript
// stores/marketStore.js
import { defineStore } from 'pinia'
import apiService from '@/services/apiService'

export const useMarketStore = defineStore('market', {
  state: () => ({
    marketData: null,
    loading: false,
    error: null,
    lastUpdated: null
  }),

  getters: {
    isDataStale: (state) => {
      if (!state.lastUpdated) return true
      const fiveMinutes = 5 * 60 * 1000
      return Date.now() - state.lastUpdated > fiveMinutes
    }
  },

  actions: {
    async fetchMarketData(symbols = ['BTC', 'ETH']) {
      this.loading = true
      this.error = null

      try {
        const response = await apiService.getMarketOverview(symbols)
        if (response.success) {
          this.marketData = response.data
          this.lastUpdated = Date.now()
        } else {
          this.error = response.message
        }
      } catch (error) {
        this.error = 'Failed to fetch market data'
        console.error('Market data fetch error:', error)
      } finally {
        this.loading = false
      }
    },

    clearError() {
      this.error = null
    }
  }
})
```

### 4. API Integration

#### Service Layer Pattern
```javascript
// services/marketService.js
import { UnifiedApiService } from './apiService'

class MarketService extends UnifiedApiService {
  async getMarketOverviewWithRetry(symbols, maxRetries = 3) {
    let lastError
    
    for (let i = 0; i < maxRetries; i++) {
      try {
        const response = await this.getMarketOverview(symbols)
        if (response.success) {
          return response
        }
        lastError = new Error(response.message)
      } catch (error) {
        lastError = error
        if (i < maxRetries - 1) {
          await this.delay(1000 * Math.pow(2, i)) // Exponential backoff
        }
      }
    }
    
    throw lastError
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
  }
}

export default new MarketService()
```

### 5. Component Development

#### Reusable Component Guidelines
```vue
<!-- components/BaseCard.vue -->
<template>
  <div class="base-card" :class="cardClasses">
    <header v-if="title || $slots.header" class="card-header">
      <slot name="header">
        <h3 class="card-title">{{ title }}</h3>
      </slot>
    </header>
    
    <main class="card-content">
      <slot></slot>
    </main>
    
    <footer v-if="$slots.footer" class="card-footer">
      <slot name="footer"></slot>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'BaseCard',
  props: {
    title: {
      type: String,
      default: ''
    },
    variant: {
      type: String,
      default: 'default',
      validator: value => ['default', 'primary', 'success', 'warning', 'danger'].includes(value)
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    cardClasses() {
      return {
        [`card--${this.variant}`]: true,
        'card--loading': this.loading
      }
    }
  }
}
</script>

<style scoped>
.base-card {
  @apply bg-white rounded-lg shadow-md overflow-hidden;
}

.card-header {
  @apply px-6 py-4 border-b border-gray-200;
}

.card-title {
  @apply text-lg font-semibold text-gray-900;
}

.card-content {
  @apply p-6;
}

.card-footer {
  @apply px-6 py-4 border-t border-gray-200 bg-gray-50;
}

.card--loading {
  @apply opacity-50 pointer-events-none;
}
</style>
```

### 6. Testing Strategy

#### Unit Testing with Vitest
```javascript
// tests/components/MarketOverview.test.js
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import MarketOverview from '@/components/MarketOverview.vue'
import { useMarketStore } from '@/stores/marketStore'

describe('MarketOverview', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders market data correctly', async () => {
    const wrapper = mount(MarketOverview)
    const store = useMarketStore()
    
    // Mock store data
    store.marketData = {
      BTC: { price: 45000, change_24h: 2.5 },
      ETH: { price: 3000, change_24h: 1.8 }
    }

    await wrapper.vm.$nextTick()

    expect(wrapper.find('[data-testid="btc-price"]').text()).toBe('$45,000.00')
    expect(wrapper.find('[data-testid="btc-change"]').text()).toBe('+2.5%')
  })

  it('shows loading state', () => {
    const wrapper = mount(MarketOverview)
    const store = useMarketStore()
    
    store.loading = true

    expect(wrapper.find('[data-testid="loading-spinner"]').exists()).toBe(true)
  })

  it('handles error state', () => {
    const wrapper = mount(MarketOverview)
    const store = useMarketStore()
    
    store.error = 'Failed to fetch data'

    expect(wrapper.find('[data-testid="error-message"]').text()).toBe('Failed to fetch data')
  })
})
```

#### Integration Testing
```javascript
// tests/integration/api.test.js
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import apiService from '@/services/apiService'

describe('API Integration', () => {
  beforeAll(() => {
    // Setup test environment
  })

  afterAll(() => {
    // Cleanup
  })

  it('fetches market overview successfully', async () => {
    const response = await apiService.getMarketOverview(['BTC', 'ETH'])
    
    expect(response.success).toBe(true)
    expect(response.data).toHaveProperty('BTC')
    expect(response.data).toHaveProperty('ETH')
    expect(response.data.BTC).toHaveProperty('price')
    expect(response.data.BTC).toHaveProperty('change_24h')
  })
})
```

### 7. Performance Optimization

#### Code Splitting
```javascript
// router/index.js
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue')
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: () => import('@/views/AnalysisView.vue')
  }
]
```

#### Lazy Loading Components
```vue
<template>
  <div>
    <Suspense>
      <template #default>
        <AsyncChart :data="chartData" />
      </template>
      <template #fallback>
        <div class="loading-spinner">Loading chart...</div>
      </template>
    </Suspense>
  </div>
</template>

<script>
import { defineAsyncComponent } from 'vue'

export default {
  components: {
    AsyncChart: defineAsyncComponent(() => import('@/components/Chart.vue'))
  }
}
</script>
```

#### Memoization and Computed Properties
```vue
<script>
import { computed, ref } from 'vue'

export default {
  setup() {
    const marketData = ref({})
    
    // Expensive computation memoized
    const sortedCoins = computed(() => {
      return Object.entries(marketData.value)
        .sort(([, a], [, b]) => b.market_cap - a.market_cap)
        .slice(0, 10)
    })
    
    return {
      marketData,
      sortedCoins
    }
  }
}
</script>
```

### 8. Build and Deployment

#### Build Configuration
```javascript
// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia'],
          charts: ['echarts'],
          ui: ['element-plus']
        }
      }
    },
    chunkSizeWarningLimit: 1000
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

#### Deployment Script Usage
```bash
# Development deployment
python scripts/deployment/deploy_frontend.py --environment development

# Production deployment
python scripts/deployment/deploy_frontend.py --environment production

# Skip tests for faster deployment
python scripts/deployment/deploy_frontend.py --environment production --skip-tests
```

### 9. Code Quality

#### ESLint Configuration
```javascript
// eslint.config.js
import js from '@eslint/js'
import vue from 'eslint-plugin-vue'

export default [
  js.configs.recommended,
  ...vue.configs['flat/recommended'],
  {
    rules: {
      'vue/multi-word-component-names': 'error',
      'vue/no-unused-vars': 'error',
      'vue/require-default-prop': 'error',
      'vue/require-prop-types': 'error',
      'no-console': 'warn',
      'no-debugger': 'error'
    }
  }
]
```

#### Prettier Configuration
```json
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "vueIndentScriptAndStyle": true
}
```

### 10. Debugging

#### Vue DevTools
- Install Vue DevTools browser extension
- Use for component inspection and state debugging
- Monitor Pinia store changes

#### Debug Configuration
```javascript
// src/config/debug.js
export const DEBUG_CONFIG = {
  enabled: import.meta.env.DEV,
  logLevel: import.meta.env.VITE_LOG_LEVEL || 'info',
  showPerformanceMetrics: import.meta.env.VITE_SHOW_PERFORMANCE === 'true'
}

export function debugLog(level, message, data = null) {
  if (!DEBUG_CONFIG.enabled) return
  
  const levels = ['error', 'warn', 'info', 'debug']
  const currentLevelIndex = levels.indexOf(DEBUG_CONFIG.logLevel)
  const messageLevelIndex = levels.indexOf(level)
  
  if (messageLevelIndex <= currentLevelIndex) {
    console[level](`[${level.toUpperCase()}]`, message, data)
  }
}
```

### 11. Monitoring and Analytics

#### Error Tracking
```javascript
// src/utils/errorHandler.js
export function setupErrorHandling() {
  window.addEventListener('error', (event) => {
    console.error('Global error:', event.error)
    // Send to error tracking service
  })

  window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason)
    // Send to error tracking service
  })
}
```

#### Performance Monitoring
```javascript
// src/utils/performance.js
export function measurePerformance(name, fn) {
  return async (...args) => {
    const start = performance.now()
    try {
      const result = await fn(...args)
      const end = performance.now()
      console.log(`${name} took ${end - start} milliseconds`)
      return result
    } catch (error) {
      const end = performance.now()
      console.error(`${name} failed after ${end - start} milliseconds`, error)
      throw error
    }
  }
}
```

## Best Practices Summary

1. **Component Design**
   - Keep components small and focused
   - Use props for data down, events for data up
   - Implement proper prop validation
   - Use scoped styles

2. **State Management**
   - Use Pinia for global state
   - Keep local state in components when appropriate
   - Implement proper error handling in stores

3. **Performance**
   - Use lazy loading for routes and components
   - Implement proper caching strategies
   - Optimize bundle size with code splitting

4. **Testing**
   - Write unit tests for components and utilities
   - Implement integration tests for critical flows
   - Use mocks for external dependencies

5. **Code Quality**
   - Follow ESLint and Prettier configurations
   - Use TypeScript for better type safety (future enhancement)
   - Write meaningful commit messages

6. **Security**
   - Validate all user inputs
   - Sanitize data before rendering
   - Use HTTPS in production
   - Implement proper CORS configuration

This workflow ensures consistent, maintainable, and high-quality frontend development for the QuantTradeSys application.