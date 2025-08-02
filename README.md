# 🚀 Vocode Analytics Dashboard

A **real-time analytics dashboard** for Vocode conversation monitoring with **financial impact tracking** and **interactive demo controls**.

## 🎯 What the CFO Sees

**Real-time financial impact analysis** showing:
- **Revenue per Minute** - $1.00 × active calls
- **Error Costs** - Financial impact of recent errors (Low: $0.68, Medium: $4.70, High: $71.50, Critical: $117.85)
- **Total ROI** - Net financial impact over application runtime
- **Live Status** - Color-coded system health (Green/Yellow/Red)

## 🚀 Quick Start

```bash
# Start the dashboard
make start

# Access the dashboard
# Open http://localhost:3001 in your browser
```

## 🎮 How to Demo

1. **Start the dashboard**: `make start`
2. **Open browser**: Go to `http://localhost:3001`
3. **Simulate scenarios**:
   - Click "Simulate Error Sequence" to see financial impact
   - Use "Add Calls" to increase revenue
   - Use "Drop Calls" to simulate system degradation
   - Click "Reset All" to start fresh

## 📊 Key Features

- **Real-time Status** - Live system health monitoring
- **Error Tracking** - 24-hour error summary with severity breakdown
- **Financial Impact** - Revenue/cost calculations and ROI tracking
- **Interactive Controls** - Error injection and call simulation for demos

## 🛠️ Essential Commands

```bash
make start        # Build & start dashboard
make stop         # Stop dashboard
make logs         # View real-time logs
make clean        # Remove all Docker resources
```

## 💰 Financial Impact System

**Revenue**: $1.00 per minute per active call
**Error Costs**:
- Low severity: $0.68 per error
- Medium severity: $4.70 per error  
- High severity: $71.50 per error
- Critical severity: $117.85 per error

**ROI Formula**: (Revenue per minute × Runtime) - Total Error Costs 