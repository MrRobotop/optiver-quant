import { useEffect, useState } from 'react';
import './index.css';

interface MarketData {
  type: string;
  symbol: string;
  timestamp_ns: number;
  bid_price: number;
  ask_price: number;
  bid_size: number;
  ask_size: number;
}

interface TradeSignal {
  type: string;
  symbol: string;
  timestamp_ns: number;
  action: 'BUY' | 'SELL';
  size: number;
  price: number;
  strategy: string;
}

function Sparkline({ data }: { data: number[] }) {
  if (!data || data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const width = 100;
  const height = 40;
  
  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((d - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg viewBox={`0 -5 ${width} ${height + 10}`} className="chart-svg" preserveAspectRatio="none" style={{ height: '40px', width: '100px' }}>
      <polyline points={points} className="chart-line" style={{ strokeWidth: 2 }} />
    </svg>
  );
}

function MainChart({ symbol, data }: { symbol: string | null, data: MarketData[] }) {
  if (!symbol || !data || data.length < 2) {
    return (
      <div className="panel" style={{ flexGrow: 1, alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ color: 'var(--text-dim)', fontSize: 18, fontWeight: 600 }}>Select a ticker to view live chart</div>
      </div>
    );
  }

  const prices = data.map(d => (d.bid_price + d.ask_price) / 2);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = max - min || 1;
  const width = 800;
  const height = 400;

  const points = prices.map((d, i) => {
    const x = (i / (prices.length - 1)) * width;
    const y = height - ((d - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');

  return (
    <div className="panel" style={{ flexGrow: 1 }}>
      <div className="panel-title">{symbol} LIVE CHART (GBM DRIFT)</div>
      <div className="chart-container">
        <svg viewBox={`0 -20 ${width} ${height + 40}`} className="chart-svg" preserveAspectRatio="none">
          {/* Axis lines */}
          <line x1="0" y1={height} x2={width} y2={height} className="chart-axis" />
          <line x1="0" y1="0" x2="0" y2={height} className="chart-axis" />
          
          <polyline points={points} className="chart-line" />
          
          {/* Current dot */}
          {points && (
             <circle 
                cx={width} 
                cy={height - ((prices[prices.length - 1] - min) / range) * height} 
                r="6" 
                className="chart-point" 
             />
          )}
        </svg>
        <div style={{ position: 'absolute', top: 20, right: 20, textAlign: 'right' }}>
           <div style={{ fontSize: 36, fontWeight: 800, color: 'var(--accent)', textShadow: '0 0 20px rgba(0,240,255,0.4)' }}>
             ${prices[prices.length - 1].toFixed(2)}
           </div>
        </div>
      </div>
    </div>
  );
}

function App() {
  const [signals, setSignals] = useState<TradeSignal[]>([]);
  const [history, setHistory] = useState<Record<string, MarketData[]>>({});
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8080/ws');
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'trade_signal') {
        setSignals(prev => [data, ...prev].slice(0, 20));
      } else if (data.type === 'market_data') {
        setHistory(prev => {
          const current = prev[data.symbol] || [];
          const next = [...current, data];
          if (next.length > 60) next.shift(); // retain 60 window points smoothly
          return { ...prev, [data.symbol]: next };
        });
      }
    };
    
    return () => ws.close();
  }, []);

  // Top active symbols prioritizing higher frequencies natively
  const activeSymbols = Object.keys(history).slice(0, 15);

  return (
    <div className="dashboard-wrapper">
      <div className="top-bar">
        <div className="brand">OPTIVER <span>QUANT</span> ENGINE</div>
        <div className="system-status">
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <span className="status-indicator"></span> PIPELINE ONLINE
          </div>
          <div style={{ color: 'var(--bg)', background: 'var(--text-dim)', padding: '2px 8px', borderRadius: 4 }}>
            Zero-Copy Vectorized
          </div>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="panel" style={{ flexGrow: 1 }}>
          <div className="panel-title">Active Markets</div>
          <div className="meter-list">
            {activeSymbols.map(sym => {
              const hist = history[sym];
              const md = hist[hist.length - 1]; // latest
              
              const obi = (md.bid_size - md.ask_size) / (md.bid_size + md.ask_size);
              const buyWidth = obi > 0 ? obi * 50 : 0;
              const sellWidth = obi < 0 ? Math.abs(obi) * 50 : 0;
              const midPrice = (md.bid_price + md.ask_price) / 2;
              const prices = hist.map(d => (d.bid_price + d.ask_price) / 2);
              
              return (
                <div 
                   key={sym} 
                   className={`meter-card ${selectedSymbol === sym ? 'active' : ''}`}
                   onClick={() => setSelectedSymbol(sym)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <div>
                        <div style={{ fontWeight: 800, fontSize: 13 }}>{sym}</div>
                        <div style={{ color: 'var(--accent)', fontVariantNumeric: 'tabular-nums', fontSize: 12, marginTop: 4, fontWeight: 700 }}>
                          ${midPrice.toFixed(2)}
                        </div>
                    </div>
                    {/* Sparkline integration */}
                    <Sparkline data={prices} />
                  </div>
                  <div className="meter-wrapper">
                    <div className="meter-center"></div>
                    {obi > 0 && <div className="meter-fill buy" style={{ width: `${buyWidth}%` }}></div>}
                    {obi < 0 && <div className="meter-fill sell" style={{ width: `${sellWidth}%` }}></div>}
                  </div>
                </div>
              );
            })}
            {activeSymbols.length === 0 && <div style={{color: 'var(--text-dim)'}}>Awaiting market streaming...</div>}
          </div>
        </div>
        
        {/* Center Panel - Main Interactive Chart */}
        <MainChart symbol={selectedSymbol} data={selectedSymbol ? history[selectedSymbol] : []} />
        
        <div className="panel" style={{ flexGrow: 1 }}>
          <div className="panel-title">Strategy Engine Feed</div>
          <div className="signal-feed">
            {signals.map((sig, i) => (
              <div key={`${sig.timestamp_ns}-${i}`} className={`signal-item ${sig.action}`}>
                <div>
                  <div className="signal-action">{sig.action} {sig.symbol}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 8, letterSpacing: 0.5 }}>{sig.strategy.toUpperCase()}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 16, fontWeight: 800 }}>${sig.price.toFixed(2)}</div>
                  <div style={{ fontSize: 11, marginTop: 6, color: 'var(--text-dim)', fontWeight: 600 }}>Sz: {sig.size.toFixed(0)}</div>
                </div>
              </div>
            ))}
            {signals.length === 0 && <div style={{color: 'var(--text-dim)'}}>Awaiting statistical arbitrages...</div>}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
