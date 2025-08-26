# 🌟 Advanced Astrology Platform

A comprehensive, modern astrology platform featuring traditional calculation methods, AI-powered interpretations, and advanced timing techniques.

## ✨ Features

### 🔮 Traditional Astrology Calculations
- **Zodiacal Releasing (ZR)** - Complete implementation with LB (Loosing of the Bond) jumps
- **Firdaria (Persian Periods)** - Weighted minor periods with proper sectarian sequences  
- **Annual Profections** - House-based timing with activated topics
- **Almuten Figuris** - Comprehensive dignity scoring with tie-breakers
- **Antiscia & Contra-Antiscia** - Solstitial and equinoctial mirror points
- **Secondary Progressions** - Day-for-a-year symbolic directions
- **Solar Arc Directions** - Precise arc-based timing
- **Transits** - Current planetary aspects and house periods
- **Midpoints** - Planetary midpoint structures and contacts
- **Fixed Stars** - Royal stars and major stellar influences

### 🤖 AI-Powered Interpretation
- **RAG-Enhanced Analysis** - Retrieval-augmented generation for accurate interpretations
- **Multi-Source Evidence** - Combines multiple timing techniques for comprehensive analysis
- **Conflict Resolution** - Intelligent handling of contradictory indications
- **Citation System** - Traceable sources for all interpretations

### 🏗️ Modern Architecture
- **FastAPI Backend** - High-performance Python API
- **Flutter Mobile App** - Cross-platform mobile application
- **Neo4j Graph Database** - Relationship-based astrological data storage
- **Redis Caching** - Optimized performance for calculations
- **Docker Deployment** - Containerized for easy deployment

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Flutter SDK (for mobile development)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/ElanurBUZLUK/astroloji.git
cd astroloji
```

2. **Start with Docker Compose**
```bash
docker-compose up -d
```

3. **Access the application**
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Development Setup

1. **Backend Development**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

2. **Mobile Development**
```bash
cd mobile/flutter_app
flutter pub get
flutter run
```

## 📊 Architecture

### Backend Components
- **Calculators** - Traditional astrology calculation engines
- **Interpreters** - AI-powered analysis and interpretation
- **RAG System** - Knowledge retrieval and citation
- **API Layer** - RESTful endpoints for all functionality

### Key Algorithms
- **LB Jump Implementation** - Proper Zodiacal Releasing sequence jumps
- **Weighted Firdaria** - Proportional minor period durations
- **Comprehensive Dignity Scoring** - Multi-factor planetary strength assessment
- **Evidence Synthesis** - Multi-technique timing correlation

## 🧪 Testing

The platform includes comprehensive test suites:

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

**Test Coverage:**
- ✅ 54+ calculator tests passing
- ✅ Golden test cases for validation
- ✅ Integration tests for API endpoints
- ✅ Edge case and boundary condition testing

## 📈 Recent Improvements

### Critical Fixes Implemented
1. **Zodiacal Releasing LB Application** - Fixed sequence jumping for authentic ZR behavior
2. **Firdaria Weighted Durations** - Corrected minor period calculations
3. **Enhanced Tone Calculation** - Comprehensive dignity and sect analysis
4. **L2 Peak Detection** - Extended peak marking to subdivision levels
5. **Comprehensive Test Suite** - 54 passing tests with golden cases

### New Calculator Modules
- Secondary Progressions with sign ingress detection
- Solar Arc Directions with exact timing
- Transit analysis with major planet emphasis
- Midpoint structures and planetary contacts
- Fixed Stars with Royal Star priority

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/astro_db
NEO4J_URI=bolt://localhost:7687
REDIS_URL=redis://localhost:6379

# API
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Swiss Ephemeris
EPHEMERIS_PATH=/path/to/swisseph/data
```

### Docker Services
- **Backend API** - Port 8000
- **PostgreSQL** - Port 5432  
- **Neo4j** - Port 7474 (HTTP), 7687 (Bolt)
- **Redis** - Port 6379

## 📚 Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [Development Plan](DEVELOPMENT_PLAN.md)
- [Astrology Fixes Summary](ASTROLOGY_FIXES_SUMMARY.md)
- [API Documentation](http://localhost:8000/docs) (when running)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Swiss Ephemeris for astronomical calculations
- Traditional astrology sources for authentic techniques
- Modern AI/ML frameworks for interpretation capabilities

---

**Built with ❤️ for the astrology community**