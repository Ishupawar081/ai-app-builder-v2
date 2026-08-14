import { useState, useEffect, useMemo } from 'react'

function App() {
  const [transactions, setTransactions] = useState([])
  const [budgets, setBudgets] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  // Modals & UI state
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [searchQuery, setSearchQuery] = useState('')
  const [sortOrder, setSortOrder] = useState('newest')
  const [chartType, setChartType] = useState('pie')
  const [timeframeFilter, setTimeframeFilter] = useState('all')

  // Load Google Fonts
  useEffect(() => {
    const link = document.createElement('link')
    link.href = 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap'
    link.rel = 'stylesheet'
    document.head.appendChild(link)
  }, [])

  // Fetch initial data from backend API
  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const res = await fetch('http://localhost:3001/api/transactions')
      if (!res.ok) throw new Error('Failed to fetch transactions')
      const data = await res.json()
      
      // If backend is empty or doesn't have seed, we can handle gracefully or seed
      if (Array.isArray(data)) {
        setTransactions(data)
        calculateBudgets(data)
      }
      setLoading(false)
    } catch (err) {
      console.warn('Backend offline or error fetching, using fallback/local state:', err)
      // Fallback seed data matching instructions
      const seedTransactions = [
        { transaction_id: '1', merchant_name: 'Grocery store', amount: 64.50, category: 'Food', transaction_type: 'Expense', date: '2023-10-15' },
        { transaction_id: '2', merchant_name: 'Monthly salary', amount: 3200.00, category: 'Income', transaction_type: 'Income', date: '2023-10-01' },
        { transaction_id: '3', merchant_name: 'Electric bill', amount: 85.20, category: 'Utilities', transaction_type: 'Expense', date: '2023-10-10' },
        { transaction_id: '4', merchant_name: 'Netflix subscription', amount: 15.99, category: 'Entertainment', transaction_type: 'Expense', date: '2023-10-12' }
      ]
      setTransactions(seedTransactions)
      calculateBudgets(seedTransactions)
      setLoading(false)
    }
  }

  const calculateBudgets = (txs) => {
    // Calculate spent amounts per category
    const categoryTotals = {}
    txs.forEach(tx => {
      if (tx.transaction_type === 'Expense') {
        categoryTotals[tx.category] = (categoryTotals[tx.category] || 0) + Number(tx.amount)
      }
    })

    // Default budget limits for categories
    const defaultLimits = {
      'Food': 300,
      'Utilities': 200,
      'Entertainment': 100,
      'Shopping': 250,
      'Other': 150
    }

    const budgetList = Object.keys(defaultLimits).map(cat => ({
      category_name: cat,
      allocated_limit: defaultLimits[cat],
      spent_amount: categoryTotals[cat] || 0
    }))

    setBudgets(budgetList)
  }

  const handleAddTransaction = async (newTx) => {
    try {
      const res = await fetch('http://localhost:3001/api/transactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTx)
      })
      if (res.ok) {
        const saved = await res.json()
        const updated = [saved, ...transactions]
        setTransactions(updated)
        calculateBudgets(updated)
      } else {
        // Fallback local update if backend write fails
        const updated = [newTx, ...transactions]
        setTransactions(updated)
        calculateBudgets(updated)
      }
    } catch (e) {
      const updated = [newTx, ...transactions]
      setTransactions(updated)
      calculateBudgets(updated)
    }
    setIsModalOpen(false)
  }

  // Filtered transactions for ledger & charts
  const filteredTransactions = useMemo(() => {
    return transactions.filter(tx => {
      const matchesCategory = selectedCategory === 'All' || tx.category === selectedCategory
      const matchesSearch = tx.merchant_name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                            tx.category.toLowerCase().includes(searchQuery.toLowerCase())
      return matchesCategory && matchesSearch
    }).sort((a, b) => {
      if (sortOrder === 'newest') return new Date(b.date) - new Date(a.date)
      if (sortOrder === 'oldest') return new Date(a.date) - new Date(b.date)
      if (sortOrder === 'highest') return b.amount - a.amount
      if (sortOrder === 'lowest') return a.amount - b.amount
      return 0
    })
  }, [transactions, selectedCategory, searchQuery, sortOrder])

  // Summary Metrics
  const totalBalance = useMemo(() => {
    return transactions.reduce((acc, tx) => {
      return tx.transaction_type === 'Income' ? acc + Number(tx.amount) : acc - Number(tx.amount)
    }, 0)
  }, [transactions])

  const totalIncome = useMemo(() => {
    return transactions
      .filter(tx => tx.transaction_type === 'Income')
      .reduce((acc, tx) => acc + Number(tx.amount), 0)
  }, [transactions])

  const totalExpense = useMemo(() => {
    return transactions
      .filter(tx => tx.transaction_type === 'Expense')
      .reduce((acc, tx) => acc + Number(tx.amount), 0)
  }, [transactions])

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#090d16',
      color: '#f8fafc',
      fontFamily: 'Inter, sans-serif',
      overflowX: 'hidden',
      paddingBottom: '64px'
    }}>
      {/* Top Navbar */}
      <nav style={{
        height: '70px',
        background: 'rgba(15, 23, 42, 0.85)',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 32px',
        position: 'sticky',
        top: 0,
        zIndex: 100
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #0f766e, #14b8a6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 8px 16px rgba(20, 184, 166, 0.3)'
          }}>
            <span style={{ fontFamily: 'Plus Jakarta Sans, sans-serif', fontWeight: 800, fontSize: '20px', color: '#fff' }}>L</span>
          </div>
          <div>
            <h1 style={{ fontFamily: 'Plus Jakarta Sans, sans-serif', fontSize: '18px', fontWeight: 700, margin: 0, letterSpacing: '-0.5px' }}>
              LedgerLens <span style={{ color: '#14b8a6', fontWeight: 500, fontSize: '14px' }}>Expense Tracker</span>
            </h1>
            <p style={{ fontSize: '11px', color: '#94a3b8', margin: 0 }}>Advanced Financial Intelligence</p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <button
            onClick={() => setIsModalOpen(true)}
            style={{
              background: 'linear-gradient(135deg, #0f766e 0%, #14b8a6 100%)',
              color: '#ffffff',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '12px',
              fontWeight: 600,
              fontSize: '14px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 4px 14px rgba(20, 184, 166, 0.4)',
              transition: 'all 0.3s ease'
            }}
            onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 6px 20px rgba(20, 184, 166, 0.6)'; }}
            onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = '0 4px 14px rgba(20, 184, 166, 0.4)'; }}
          >
            <span style={{ fontSize: '18px', lineHeight: 0 }}>+</span> Add Transaction
          </button>
        </div>
      </nav>

      {/* Main Dashboard Layout */}
      <main style={{ maxWidth: '1400px', margin: '32px auto', padding: '0 24px' }}>
        
        {/* KPI Summary Cards */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '24px',
          marginBottom: '32px'
        }}>
          <KPICard 
            title="Total Balance" 
            amount={totalBalance} 
            type="balance" 
            icon="💎" 
            trend="+4.2% this month" 
          />
          <KPICard 
            title="Monthly Income" 
            amount={totalIncome} 
            type="income" 
            icon="📈" 
            trend="Stable cashflow" 
          />
          <KPICard 
            title="Total Expenses" 
            amount={totalExpense} 
            type="expense" 
            icon="📉" 
            trend="Within safe margin" 
          />
        </div>

        {/* Category Filter Bar */}
        <div style={{ marginBottom: '24px' }}>
          <CategoryFilter 
            selectedCategory={selectedCategory} 
            onSelectCategory={setSelectedCategory} 
            transactions={transactions} 
          />
        </div>

        {/* Core Feature Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
          gap: '24px',
          marginBottom: '32px'
        }}>
          {/* Feature 1: Spending Chart */}
          <SpendingChart 
            transactions={transactions} 
            selectedCategory={selectedCategory}
            chartType={chartType}
            setChartType={setChartType}
            timeframeFilter={timeframeFilter}
            setTimeframeFilter={setTimeframeFilter}
          />

          {/* Feature 2: Budget Limit Tracking */}
          <BudgetProgressCard 
            budgets={budgets} 
            warningThreshold={80} 
          />
        </div>

        {/* Feature 3: Searchable & Filterable Transaction Ledger */}
        <TransactionList 
          transactions={filteredTransactions}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          sortOrder={sortOrder}
          setSortOrder={setSortOrder}
          selectedCategory={selectedCategory}
        />
      </main>

      {/* Add Transaction Modal Component */}
      {isModalOpen && (
        <AddTransactionModal 
          onClose={() => setIsModalOpen(false)} 
          onSubmit={handleAddTransaction} 
        />
      )}
    </div>
  )
}

// --- SUB-COMPONENTS ---

function KPICard({ title, amount, type, icon, trend }) {
  const isNegative = amount < 0
  return (
    <div style={{
      background: 'rgba(30, 41, 59, 0.6)',
      backdropFilter: 'blur(16px)',
      border: '1px solid rgba(255, 255, 255, 0.08)',
      borderRadius: '20px',
      padding: '24px',
      position: 'relative',
      overflow: 'hidden',
      boxShadow: '0 10px 30px rgba(0, 0, 0, 0.3)',
      transition: 'all 0.3s ease'
    }}
    onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-4px)'; e.currentTarget.style.borderColor = 'rgba(20, 184, 166, 0.4)'; }}
    onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)'; }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
        <span style={{ fontSize: '13px', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          {title}
        </span>
        <div style={{
          width: '40px',
          height: '40px',
          borderRadius: '12px',
          background: 'rgba(255, 255, 255, 0.05)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '18px'
        }}>
          {icon}
        </div>
      </div>
      <div style={{
        fontFamily: 'Plus Jakarta Sans, sans-serif',
        fontSize: '32px',
        fontWeight: 700,
        color: type === 'balance' && isNegative ? '#f43f5e' : '#f8fafc',
        marginBottom: '8px'
      }}>
        ${Math.abs(amount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#14b8a6', fontWeight: 500 }}>
        <span>{trend}</span>
      </div>
    </div>
  )
}

function CategoryFilter({ selectedCategory, onSelectCategory, transactions }) {
  const categories = ['All', 'Food', 'Income', 'Utilities', 'Entertainment', 'Shopping', 'Other']

  return (
    <div style={{
      background: 'rgba(30, 41, 59, 0.4)',
      backdropFilter: 'blur(12px)',
      border: '1px solid rgba(255, 255, 255, 0.06)',
      borderRadius: '16px',
      padding: '16px 20px',
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      overflowX: 'auto'
    }}>
      <span style={{ fontSize: '13px', fontWeight: 600, color: '#94a3b8', whiteSpace: 'nowrap' }}>Filter Category:</span>
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        {categories.map(cat => {
          const isActive = selectedCategory === cat
          return (
            <button
              key={cat}
              onClick={() => onSelectCategory(cat)}
              style={{
                background: isActive ? 'linear-gradient(135deg, #0f766e, #14b8a6)' : 'rgba(255, 255, 255, 0.05)',
                color: isActive ? '#ffffff' : '#cbd5e1',
                border: isActive ? 'none' : '1px solid rgba(255, 255, 255, 0.08)',
                padding: '8px 16px',
                borderRadius: '10px',
                fontWeight: 600,
                fontSize: '13px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                whiteSpace: 'nowrap',
                boxShadow: isActive ? '0 4px 12px rgba(20, 184, 166, 0.3)' : 'none'
              }}
              onMouseEnter={e => { if (!isActive) e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)' }}
              onMouseLeave={e => { if (!isActive) e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)' }}
            >
              {cat}
            </button>
          )
        })}
      </div>
    </div>
  )
}

function SpendingChart({ transactions, selectedCategory, chartType, setChartType, timeframeFilter, setTimeframeFilter }) {
  // Aggregate expenses by category with real-time recalculation
  const categoryData = useMemo(() => {
    const expenses = transactions.filter(tx => tx.transaction_type === 'Expense')
    const map = {}
    expenses.forEach(tx => {
      map[tx.category] = (map[tx.category] || 0) + Number(tx.amount)
    })
    return Object.keys(map).map(cat => ({ category: cat, amount: map[cat] })).sort((a, b) => b.amount - a.amount)
  }, [transactions])

  const totalExpenseSum = categoryData.reduce((acc, curr) => acc + curr.amount, 0)

  const colors = ['#14b8a6', '#0f766e', '#f59e0b', '#3b82f6', '#8b5cf6', '#ec4899']

  return (
    <div style={{
      background: 'rgba(30, 41, 59, 0.6)',
      backdropFilter: 'blur(16px)',
      border: '1px solid rgba(255, 255, 255, 0.08)',
      borderRadius: '24px',
      padding: '28px',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      boxShadow: '0 10px 30px rgba(0, 0, 0, 0.3)'
    }}>
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h3 style={{ fontFamily: 'Plus Jakarta Sans, sans-serif', fontSize: '18px', fontWeight: 700, margin: 0 }}>
              Spending Breakdown
            </h3>
            <p style={{ fontSize: '12px', color: '#94a3b8', margin: '4px 0 0 0' }}>Real-time category expenditure proportion</p>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => setChartType(chartType === 'pie' ? 'bar' : 'pie')}
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                color: '#cbd5e1',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                padding: '6px 12px',
                borderRadius: '8px',
                fontSize: '12px',
                cursor: 'pointer',
                fontWeight: 600
              }}
            >
              {chartType === 'pie' ? 'Bar View' : 'Proportional View'}
            </button>
          </div>
        </div>

        {categoryData.length === 0 ? (
          <div style={{ padding: '60px 0', textAlign: 'center', color: '#64748b' }}>
            <p style={{ fontSize: '14px', margin: 0 }}>No expense data available for visualization.</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', margin: '20px 0' }}>
            {categoryData.map((item, index) => {
              const percentage = totalExpenseSum > 0 ? ((item.amount / totalExpenseSum) * 100).toFixed(1) : 0
              const color = colors[index % colors.length]
              return (
                <div key={item.category} style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: 600 }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: color }}></span>
                      {item.category}
                    </span>
                    <span>${item.amount.toLocaleString('en-US', { minimumFractionDigits: 2 })} <span style={{ color: '#94a3b8', fontWeight: 400 }}>({percentage}%)</span></span>
                  </div>
                  <div style={{
                    width: '100%',
                    height: '8px',
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    borderRadius: '4px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${percentage}%`,
                      height: '100%',
                      backgroundColor: color,
                      borderRadius: '4px',
                      transition: 'width 0.5s ease'
                    }}></div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      <div style={{
        borderTop: '1px solid rgba(255, 255, 255, 0.06)',
        paddingTop: '16px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        fontSize: '13px',
        color: '#94a3b8'
      }}>
        <span>Total Tracked Expenses</span>
        <span style={{ fontFamily: 'Plus Jakarta Sans, sans-serif', fontWeight: 700, color: '#f8fafc', fontSize: '16px' }}>
          ${totalExpenseSum.toLocaleString('en-US', { minimumFractionDigits: 2 })}
        </span>
      </div>
    </div>
  )
}

function BudgetProgressCard({ budgets, warningThreshold }) {
  return (
    <div style={{
      background: 'rgba(30, 41, 59, 0.6)',
      backdropFilter: 'blur(16px)',
      border: '1px solid rgba(255, 255, 255, 0.08)',
      borderRadius: '24px',
      padding: '28px',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      boxShadow: '0 10px 30px rgba(0, 0, 0, 0.3)'
    }}>
      <div>
        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ fontFamily: 'Plus Jakarta Sans, sans-serif', fontSize: '18px', fontWeight: 700, margin: 0 }}>
            Budget Limits & Warnings
          </h3>
          <p style={{ fontSize: '12px', color: '#94a3b8', margin: '4px 0 0 0' }}>Automated alerts when exceeding {warningThreshold}% threshold</p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', maxHeight: '310px', overflowY: 'auto', paddingRight: '4px' }}>
          {budgets.map(b => {
            const percentage = b.allocated_limit > 0 ? (b.spent_amount / b.allocated_limit) * 100 : 0
            const isOverBudget = percentage >= warningThreshold
            const isCritical = percentage >= 100

            return (
              <div key={b.category_name} style={{
                background: isOverBudget ? 'rgba(244, 63, 94, 0.06)' : 'rgba(255, 255, 255, 0.02)',
                border: `1px solid ${isOverBudget ? 'rgba(244, 63, 94, 0.3)' : 'rgba(255, 255, 255, 0.06)'}`,
                borderRadius: '14px',
                padding: '14px 16px',
                transition: 'all 0.2s ease'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: 600, fontSize: '14px' }}>{b.category_name}</span>
                    {isOverBudget && (
                      <span style={{
                        backgroundColor: isCritical ? '#f43f5e' : '#f59e0b',
                        color: '#000',
                        fontSize: '10px',
                        fontWeight: 700,
                        padding: '2px 6px',
                        borderRadius: '6px',
                        textTransform: 'uppercase'
                      }}>
                        {isCritical ? 'Over Budget' : 'Warning'}
                      </span>
                    )}
                  </div>
                  <span style={{ fontSize: '13px', fontWeight: 600, color: isOverBudget ? '#f43f5e' : '#cbd5e1' }}>
                    ${b.spent_amount.toFixed(2)} <span style={{ color: '#94a3b8', fontWeight: 400 }}>/ ${b.allocated_limit}</span>
                  </span>
                </div>
                
                <div style={{
                  width: '100%',
                  height: '8px',
                  backgroundColor: 'rgba(255, 255, 255, 0.05)',
                  borderRadius: '4px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    width: `${Math.min(percentage, 100)}%`,
                    height: '100%',
                    backgroundColor: isCritical ? '#f43f5e' : isOverBudget ? '#f59e0b' : '#14b8a6',
                    borderRadius: '4px',
                    transition: 'width 0.4s ease'
                  }}></div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function TransactionList({ transactions, searchQuery, setSearchQuery, sortOrder, setSortOrder, selectedCategory }) {
  return (
    <div style={{
      background: 'rgba(30, 41, 59, 0.6)',
      backdropFilter: 'blur(16px)',
      border: '1px solid rgba(255, 255, 255, 0.08)',
      borderRadius: '24px',
      padding: '28px',
      boxShadow: '0 10px 30px rgba(0, 0, 0, 0.3)'
    }}>
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '16px',
        marginBottom: '24px'
      }}>
        <div>
          <h3 style={{ fontFamily: 'Plus Jakarta Sans, sans-serif', fontSize: '18px', fontWeight: 700, margin: 0 }}>
            Transaction Ledger
          </h3>
          <p style={{ fontSize: '12px', color: '#94a3b8', margin: '4px 0 0 0' }}>Searchable and filterable activity feed</p>
        </div>

        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
          {/* Search bar */}
          <div style={{ position: 'relative' }}>
            <span style={{ position: 'absolute', left: '12px', top: '10px', color: '#94a3b8', fontSize: '14px' }}>🔍</span>
            <input
              type="text"
              placeholder="Search merchant..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              style={{
                background: 'rgba(15, 23, 42, 0.6)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '12px',
                padding: '10px 14px 10px 36px',
                color: '#fff',
                fontSize: '13px',
                outline: 'none',
                width: '220px',
                transition: 'all 0.2s ease'
              }}
              onFocus={e => e.target.style.borderColor = '#14b8a6'}
              onBlur={e => e.target.style.borderColor = 'rgba(255, 255, 255, 0.1)'}
            />
          </div>

          {/* Sort Order Selector */}
          <select
            value={sortOrder}
            onChange={e => setSortOrder(e.target.value)}
            style={{
              background: 'rgba(15, 23, 42, 0.6)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '12px',
              padding: '10px 14px',
              color: '#fff',
              fontSize: '13px',
              outline: 'none',
              cursor: 'pointer'
            }}
          >
            <option value="newest" style={{ background: '#0f172a' }}>Newest First</option>
            <option value="oldest" style={{ background: '#0f172a' }}>Oldest First</option>
            <option value="highest" style={{ background: '#0f172a' }}>Highest Amount</option>
            <option value="lowest" style={{ background: '#0f172a' }}>Lowest Amount</option>
          </select>
        </div>
      </div>

      {transactions.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '60px 20px',
          background: 'rgba(255, 255, 255, 0.02)',
          borderRadius: '16px',
          border: '1px dashed rgba(255, 255, 255, 0.08)'
        }}>
          <div style={{ fontSize: '32px', marginBottom: '12px' }}>📂</div>
          <h4 style={{ fontFamily: 'Plus Jakarta Sans, sans-serif', fontSize: '16px', fontWeight: 600, margin: '0 0 4px 0' }}>No transactions found</h4>
          <p style={{ fontSize: '13px', color: '#94a3b8', margin: 0 }}>Try adjusting your search query or category filter.</p>
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.08)', color: '#94a3b8', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Merchant / Description</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Category</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Type</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Date</th>
                <th style={{ padding: '12px 16px', fontWeight: 600, textAlign: 'right' }}>Amount</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map(tx => {
                const isIncome = tx.transaction_type === 'Income'
                return (
                  <tr 
                    key={tx.transaction_id || Math.random()} 
                    style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)', transition: 'background 0.2s ease' }}
                    onMouseEnter={e => e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.02)'}
                    onMouseLeave={e => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    <td style={{ padding: '16px', fontWeight: 600, color: '#f8fafc' }}>
                      {tx.merchant_name}
                    </td>
                    <td style={{ padding: '16px' }}>
                      <span style={{
                        background: 'rgba(20, 184, 166, 0.1)',
                        color: '#14b8a6',
                        padding: '4px 10px',
                        borderRadius: '8px',
                        fontSize: '12px',
                        fontWeight: 600
                      }}>
                        {tx.category}
                      </span>
                    </td>
                    <td style={{ padding: '16px' }}>
                      <span style={{
                        color: isIncome ? '#34d399' : '#f43f5e',
                        fontWeight: 600,
                        fontSize: '13px'
                      }}>
                        {tx.transaction_type}
                      </span>
                    </td>
                    <td style={{ padding: '16px', color: '#94a3b8', fontSize: '13px' }}>
                      {tx.date}
                    </td>
                    <td style={{ padding: '16px', textAlign: 'right', fontFamily: 'Plus Jakarta Sans, sans-serif', fontWeight: 700, fontSize: '15px', color: isIncome ? '#34d399' : '#f8fafc' }}>
                      {isIncome ? '+' : '-'}${Number(tx.amount).toFixed(2)}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function AddTransactionModal({ onClose, onSubmit }) {
  const [amount, setAmount] = useState('')
  const [merchantName, setMerchantName] = useState('')
  const [category, setCategory] = useState('Food')
  const [transactionType, setTransactionType] = useState('Expense')
  const [date, setDate] = useState(new Date().toISOString().split('T')[0])
  const [errorMsg, setErrorMsg] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!merchantName.trim()) {
      setErrorMsg('Please enter a merchant name.')
      return
    }
    if (!amount || isNaN(amount) || Number(amount) <= 0) {
      setErrorMsg('Please enter a valid positive amount.')
      return
    }

    const newTx = {
      transaction_id: 'tx_' + Date.now(),
      merchant_name: merchantName.trim(),
      amount: parseFloat(amount),
      category: transactionType === 'Income' ? 'Income' : category,
      transaction_type: transactionType,
      date
    }

    onSubmit(newTx)
  }

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      backgroundColor: 'rgba(5, 9, 18, 0.8)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '16px'
    }}>
      <div style={{
        background: '#0f172a',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '24px',
        width: '100%',
        maxWidth: '480px',
        padding: '32px',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6)',
        position: 'relative'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <div>
            <h3 style={{ fontFamily: 'Plus Jakarta Sans, sans-serif', fontSize: '20px', fontWeight: 700, margin: 0 }}>
              New Transaction
            </h3>
            <p style={{ fontSize: '13px', color: '#94a3b8', margin: '4px 0 0 0' }}>Record income or expense item</p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: 'none',
              color: '#94a3b8',
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              cursor: 'pointer',
              fontWeight: 700,
              fontSize: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            &times;
          </button>
        </div>

        {errorMsg && (
          <div style={{
            background: 'rgba(244, 63, 94, 0.1)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            color: '#f43f5e',
            padding: '10px 14px',
            borderRadius: '10px',
            fontSize: '13px',
            marginBottom: '16px',
            fontWeight: 500
          }}>
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '6px', textTransform: 'uppercase' }}>
              Transaction Type
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <button
                type="button"
                onClick={() => setTransactionType('Expense')}
                style={{
                  background: transactionType === 'Expense' ? '#f43f5e' : 'rgba(255, 255, 255, 0.05)',
                  color: transactionType === 'Expense' ? '#fff' : '#94a3b8',
                  border: 'none',
                  padding: '12px',
                  borderRadius: '12px',
                  fontWeight: 600,
                  fontSize: '14px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                Expense
              </button>
              <button
                type="button"
                onClick={() => setTransactionType('Income')}
                style={{
                  background: transactionType === 'Income' ? '#10b981' : 'rgba(255, 255, 255, 0.05)',
                  color: transactionType === 'Income' ? '#fff' : '#94a3b8',
                  border: 'none',
                  padding: '12px',
                  borderRadius: '12px',
                  fontWeight: 600,
                  fontSize: '14px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                Income
              </button>
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '6px', textTransform: 'uppercase' }}>
              Merchant / Title
            </label>
            <input
              type="text"
              placeholder="e.g. Whole Foods, Monthly Salary"
              value={merchantName}
              onChange={e => setMerchantName(e.target.value)}
              style={{
                width: '100%',
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '12px',
                padding: '12px 16px',
                color: '#fff',
                fontSize: '14px',
                outline: 'none',
                boxSizing: 'border-box'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '6px', textTransform: 'uppercase' }}>
              Amount ($)
            </label>
            <input
              type="number"
              step="0.01"
              placeholder="0.00"
              value={amount}
              onChange={e => setAmount(e.target.value)}
              style={{
                width: '100%',
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '12px',
                padding: '12px 16px',
                color: '#fff',
                fontSize: '14px',
                outline: 'none',
                boxSizing: 'border-box'
              }}
            />
          </div>

          {transactionType === 'Expense' && (
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '6px', textTransform: 'uppercase' }}>
                Category
              </label>
              <select
                value={category}
                onChange={e => setCategory(e.target.value)}
                style={{
                  width: '100%',
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '12px',
                  padding: '12px 16px',
                  color: '#fff',
                  fontSize: '14px',
                  outline: 'none',
                  boxSizing: 'border-box'
                }}
              >
                <option value="Food" style={{ background: '#0f172a' }}>Food</option>
                <option value="Utilities" style={{ background: '#0f172a' }}>Utilities</option>
                <option value="Entertainment" style={{ background: '#0f172a' }}>Entertainment</option>
                <option value="Shopping" style={{ background: '#0f172a' }}>Shopping</option>
                <option value="Other" style={{ background: '#0f172a' }}>Other</option>
              </select>
            </div>
          )}

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '6px', textTransform: 'uppercase' }}>
              Date
            </label>
            <input
              type="date"
              value={date}
              onChange={e => setDate(e.target.value)}
              style={{
                width: '100%',
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '12px',
                padding: '12px 16px',
                color: '#fff',
                fontSize: '14px',
                outline: 'none',
                boxSizing: 'border-box'
              }}
            />
          </div>

          <button
            type="submit"
            style={{
              background: 'linear-gradient(135deg, #0f766e 0%, #14b8a6 100%)',
              color: '#fff',
              border: 'none',
              padding: '14px',
              borderRadius: '12px',
              fontWeight: 700,
              fontSize: '15px',
              cursor: 'pointer',
              marginTop: '12px',
              boxShadow: '0 4px 14px rgba(20, 184, 166, 0.4)',
              transition: 'all 0.2s ease'
            }}
          >
            Save Transaction
          </button>
        </form>
      </div>
    </div>
  )
}

export default App