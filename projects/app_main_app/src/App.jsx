import { useState } from 'react'

function App() {
  const [items, setItems] = useState([])
  const [input, setInput] = useState('')
  const [hover, setHover] = useState(null)

  const add = () => {
    if (!input.trim()) return
    setItems([...items, { id: Date.now(), text: input.trim() }])
    setInput('')
  }

  const remove = (id) => setItems(items.filter(i => i.id !== id))

  return (
    <div style={{ minHeight: '100vh', background: '#0f172a', display: 'flex', justifyContent: 'center', alignItems: 'flex-start', padding: '60px 24px', fontFamily: 'Inter, sans-serif' }}>
      <div style={{ width: '100%', maxWidth: '560px' }}>
        <h1 style={{ color: '#f1f5f9', fontSize: '28px', fontWeight: 700, marginBottom: '8px' }}>App</h1>
        <p style={{ color: '#64748b', marginBottom: '32px' }}>Add items below to get started.</p>
        <div style={{ display: 'flex', gap: '10px', marginBottom: '24px' }}>
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && add()}
            placeholder="Type something …"
            style={{ flex: 1, padding: '12px 16px', background: '#1e293b', border: '1px solid #334155', borderRadius: '10px', color: '#f1f5f9', fontSize: '15px', outline: 'none' }}
          />
          <button onClick={add} style={{ padding: '12px 20px', background: '#6366f1', color: '#fff', border: 'none', borderRadius: '10px', cursor: 'pointer', fontWeight: 600, fontSize: '15px' }}>Add</button>
        </div>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {items.map(item => (
            <li key={item.id}
              style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 18px', background: hover === item.id ? '#1e293b' : '#111827', borderRadius: '10px', border: '1px solid #1e293b', transition: 'all 0.15s ease' }}
              onMouseEnter={() => setHover(item.id)}
              onMouseLeave={() => setHover(null)}
            >
              <span style={{ color: '#e2e8f0' }}>{item.text}</span>
              <button onClick={() => remove(item.id)} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '20px', lineHeight: 1 }}>×</button>
            </li>
          ))}
        </ul>
        {items.length === 0 && (
          <p style={{ color: '#334155', textAlign: 'center', marginTop: '40px' }}>No items yet. Add one above ↑</p>
        )}
      </div>
    </div>
  )
}

export default App
