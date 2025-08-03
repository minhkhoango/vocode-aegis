# 🚀 Vocode Analytics Dashboard

Real-time analytics dashboard for Vocode conversation monitoring with financial impact tracking.

## 🎯 Features

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

## 🌐 Public Access

```bash
make tunnel
```

Creates secure public URL via Cloudflare tunnel.

## 🎮 Demo

1. **Start**: `make start`
2. **Open**: `http://localhost:3001`
3. **Simulate**: Click "Simulate Error Sequence", "Add Calls", "Drop Calls", "Reset All"

## 🛠️ Commands

```bash
make start        # Start dashboard
make stop         # Stop dashboard
make logs         # View logs
make clean        # Remove all resources
make tunnel       # Create public tunnel
``` 