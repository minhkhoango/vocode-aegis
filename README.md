# 🚀 Vocode Analytics Dashboard

Real-time analytics dashboard for Vocode conversation monitoring with financial impact tracking.

## 🎯 What the CFO Sees

**Real-time financial impact analysis**:
- **Revenue per Minute** - $1.00 × active calls
- **Error Costs** - Low: $0.68, Medium: $4.70, High: $71.50, Critical: $117.85
- **Total ROI** - Net financial impact over runtime
- **Live Status** - Color-coded health (Green/Yellow/Red)

## 🚀 Quick Start

```bash
git clone https://github.com/minhkhoango/vocode-aegis.git
cd vocode-aegis
make start
```

Access at `http://localhost:3001`

## 🎮 Demo

1. **Start**: `make start`
2. **Open**: `http://localhost:3001`
3. **Simulate**:
   - Click "Simulate Error Sequence"
   - Use "Add Calls" to increase revenue
   - Use "Drop Calls" to simulate degradation
   - Click "Reset All" to start fresh

## 🛠️ Commands

```bash
make start        # Start dashboard
make stop         # Stop dashboard
make logs         # View logs
make clean        # Remove all resources
``` 