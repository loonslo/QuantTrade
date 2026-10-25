# Frontend Documentation

## Overview

The QuantTradeSys frontend is a Vue.js application located in `frontend/crypto-report/`. It provides a modern, responsive web interface for cryptocurrency trading analysis and strategy management.

## Architecture

### Technology Stack

- **Framework**: Vue.js 3.5+
- **Build Tool**: Vite 7.0+
- **UI Library**: Element Plus 2.10+
- **State Management**: Pinia 3.0+
- **Routing**: Vue Router 4.5+
- **Charts**: ECharts 5.5+
- **HTTP Client**: Axios 1.11+
- **Icons**: Iconify Vue 4.1+

### Project Structure

```
frontend/crypto-report/
├── src/
│   ├── components/          # Reusable Vue components
│   │   ├── CoinAnalysis.vue
│   │   ├── MarketAnalysis.vue
│   │   ├── MarketOverview.vue
│   │   ├── Navigation.vue
│   │   ├── StrategyConfig.vue
│   │   ├── TechnicalAnalysis.vue
│   │   └── icons/           # Icon components
│   ├── views/               # Page components
│   │   ├── HomeView.vue
│   │   ├── AboutView.vue
│   │   └── CryptoReport.vue
│   ├── stores/              # Pinia stores
│   │   ├── counter.js
│   │   └── cryptoStore.js
│   ├── services/            # API services
│   │   └── apiService.js
│   ├── config/              # Configuration
│   │   └── app.config.js
│   ├── router/              # Vue Router configuration
│   │   └── index.js
│   ├── assets/              # Static assets
│   │   ├── base.css
│   │   ├── main.css
│   │   └── logo.svg
│   ├── plugins/             # Vue plugins
│   │   └── vuetify.js
│   ├── App.vue              # Root component
│   └── main.js              # Application entry point
├── public/                  # Static public assets
├── dist/                    # Build output (generated)
├── node_modules/            # Dependencies (generated)
├── package.json             # Project configuration
├── package-lock.json        # Dependency lock file
├── vite.config.js           # Vite configuration
├── eslint.config.js         # ESLint configuration
├── .prettierrc.json         # Prettier configuration
├── .gitignore               # Git ignore rules
├── index.html               # HTML template
└── README.md                # Project documentation
```

## Development Setup

### Prerequisites

- Node.js 18+ (recommended: 20.19.0 or 22.12.0+)
- npm 8+ or yarn 1.22+

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend/crypto-report
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start development server:
   ```bash
   npm run dev
   ```

4. Open browser to `http://localhost:5173`

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run format` - Format code with Prettier

### Using Development Scripts

You can also use the provided Python scripts for easier development:

```bash
# Start frontend development server
python scripts/dev/start_frontend.py

# Deploy frontend for production
python scripts/deployment/deploy_frontend.py --environment production
```

## Configuration

### Environment Variables

The frontend uses Vite's environment variable system. Create `.env.local` for local development:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCK_DATA=false
```

### API Configuration

The API configuration is centralized in `src/config/app.config.js`:

```javascript
export const APP_CONFIG = {
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  USE_MOCK_DATA: import.meta.env.VITE_USE_MOCK_DATA === 'true',
  TIMEOUT: 30000
}
```

## API Integration

### Service Architecture

The frontend uses a modular API service architecture with the following services:

- **MarketDataService** - Market data and pricing
- **MarketAnalysisService** - Technical analysis and strategies
- **TechnicalAnalysisService** - Technical indicators
- **AdvancedMarketDataService** - Advanced market data features

### API Endpoints

#### Market Data
- `GET /api/market-data/trend/24h/{symbol}` - 24-hour trend data
- `POST /api/market-data/batch/prices` - Batch price data
- `POST /api/market-data/advanced/overview` - Market overview
- `POST /api/market-data/advanced/coins` - Coin market data
- `GET /api/market-data/advanced/fear-greed` - Fear & Greed Index

#### Market Analysis
- `GET /api/market-analysis/technical/{symbol}` - Technical analysis
- `GET /api/market-analysis/support-resistance/{symbol}` - Support/Resistance levels
- `POST /api/market-analysis/strategy/backtest` - Strategy backtesting
- `POST /api/market-analysis/strategy/optimize` - Strategy optimization
- `GET /api/market-analysis/strategies` - Available strategies

### Error Handling

The API service includes comprehensive error handling:

```javascript
async request(endpoint, options = {}) {
  try {
    const response = await fetch(url, config)
    if (!response.ok) {
      return { 
        success: false, 
        data: {}, 
        message: `HTTP错误 ${response.status}`, 
        error: `HTTP ${response.status}` 
      }
    }
    return await response.json()
  } catch (error) {
    return { 
      success: false, 
      data: {}, 
      message: "网络请求失败", 
      error: error.message 
    }
  }
}
```

## State Management

### Pinia Stores

The application uses Pinia for state management:

#### CryptoStore
Manages cryptocurrency data and market information:

```javascript
export const useCryptoStore = defineStore('crypto', {
  state: () => ({
    marketData: {},
    selectedSymbol: 'BTC',
    loading: false,
    error: null
  }),
  
  actions: {
    async fetchMarketData() {
      // Fetch market data logic
    }
  }
})
```

## Components

### Core Components

#### MarketOverview
Displays overall market statistics and trends.

#### CoinAnalysis
Shows detailed analysis for individual cryptocurrencies.

#### TechnicalAnalysis
Renders technical indicators and charts.

#### StrategyConfig
Provides strategy configuration interface.

### Component Guidelines

1. **Props Validation**: Always define prop types and defaults
2. **Event Naming**: Use kebab-case for custom events
3. **Styling**: Use scoped styles with CSS modules
4. **Accessibility**: Include proper ARIA labels and keyboard navigation

## Styling

### CSS Architecture

- **Base Styles**: `src/assets/base.css` - CSS reset and base styles
- **Main Styles**: `src/assets/main.css` - Global application styles
- **Component Styles**: Scoped styles within each component

### Design System

The application follows a consistent design system:

- **Colors**: Primary blue (#409EFF), success green (#67C23A), warning orange (#E6A23C)
- **Typography**: System fonts with fallbacks
- **Spacing**: 8px grid system
- **Breakpoints**: Mobile-first responsive design

## Build and Deployment

### Production Build

```bash
npm run build
```

This creates optimized files in the `dist/` directory.

### Deployment Options

1. **Static Hosting**: Deploy `dist/` folder to any static hosting service
2. **CDN**: Upload assets to CDN for better performance
3. **Docker**: Use provided Dockerfile for containerized deployment

### Performance Optimization

- **Code Splitting**: Automatic route-based code splitting
- **Tree Shaking**: Unused code elimination
- **Asset Optimization**: Image and CSS optimization
- **Caching**: Proper cache headers for static assets

## Testing

### Testing Strategy

- **Unit Tests**: Component logic testing
- **Integration Tests**: API integration testing
- **E2E Tests**: User workflow testing

### Running Tests

```bash
npm run test        # Run unit tests
npm run test:e2e    # Run E2E tests
npm run coverage    # Generate coverage report
```

## Troubleshooting

### Common Issues

1. **API Connection Errors**
   - Check `VITE_API_BASE_URL` environment variable
   - Verify backend server is running
   - Check CORS configuration

2. **Build Failures**
   - Clear node_modules and reinstall dependencies
   - Check Node.js version compatibility
   - Verify all imports are correct

3. **Development Server Issues**
   - Check port availability (default: 5173)
   - Clear Vite cache: `rm -rf node_modules/.vite`
   - Restart development server

### Debug Mode

Enable debug mode by setting:
```env
VITE_DEBUG=true
```

This enables additional console logging and development tools.

## Contributing

### Code Style

- Use ESLint and Prettier for code formatting
- Follow Vue.js style guide
- Write meaningful commit messages
- Add JSDoc comments for complex functions

### Pull Request Process

1. Create feature branch from `main`
2. Make changes with proper testing
3. Run linting and tests
4. Submit pull request with description
5. Address review feedback

## Resources

- [Vue.js Documentation](https://vuejs.org/)
- [Vite Documentation](https://vitejs.dev/)
- [Element Plus Documentation](https://element-plus.org/)
- [Pinia Documentation](https://pinia.vuejs.org/)
- [ECharts Documentation](https://echarts.apache.org/)