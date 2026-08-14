import express from 'express';
import cors from 'cors';

const app =express();

app.use(cors());
app.use(express.json());

let transactions = [
  {
    transaction_id: '1',
    merchant_name: 'Grocery store',
    amount: 64.50,
    category: 'Food',
    transaction_type: 'Expense',
    date: new Date().toISOString()
  },
  {
    transaction_id: '2',
    merchant_name: 'Monthly salary',
    amount: 3200.00,
    category: 'Income',
    transaction_type: 'Income',
    date: new Date().toISOString()
  },
  {
    transaction_id: '3',
    merchant_name: 'Electric bill',
    amount: 85.20,
    category: 'Utilities',
    transaction_type: 'Expense',
    date: new Date().toISOString()
  },
  {
    transaction_id: '4',
    merchant_name: 'Netflix subscription',
    amount: 15.99,
    category: 'Entertainment',
    transaction_type: 'Expense',
    date: new Date().toISOString()
  }
];

let budgetLimits = [
  { category_name: 'Food', allocated_limit: 300, spent_amount: 64.50 },
  { category_name: 'Utilities', allocated_limit: 150, spent_amount: 85.20 },
  { category_name: 'Entertainment', allocated_limit: 50, spent_amount: 15.99 }
];

app.get('/api/transactions', (req, res) => {
  const { category, date } = req.query;
  let results = [...transactions];

  if (category) {
    results = results.filter(t => t.category.toLowerCase() === category.toLowerCase());
  }

  if (date) {
    results = results.filter(t => t.date.startsWith(date));
  }

  res.json(results);
});

app.post('/api/transactions', (req, res) => {
  const { merchant_name, amount, category, transaction_type, date } = req.body;

  if (!merchant_name || typeof amount !== 'number' || !category || !transaction_type) {
    return res.status(400).json({ error: 'Missing required fields or invalid amount type' });
  }

  const newTransaction = {
    transaction_id: Date.now().toString(),
    merchant_name,
    amount,
    category,
    transaction_type,
    date: date || new Date().toISOString()
  };

  transactions.push(newTransaction);

  if (transaction_type.toLowerCase() === 'expense') {
    const budget = budgetLimits.find(b => b.category_name.toLowerCase() === category.toLowerCase());
    if (budget) {
      budget.spent_amount += amount;
    } else {
      budgetLimits.push({
        category_name: category,
        allocated_limit: 200, 
        spent_amount: amount
      });
    }
  }

  res.status(201).json(newTransaction);
});

app.get('/api/budgets/summary', (req, res) => {
  const expenseTransactions = transactions.filter(t => t.transaction_type.toLowerCase() === 'expense');
  
  const spentMap = {};
  expenseTransactions.forEach(t => {
    spentMap[t.category] = (spentMap[t.category] || 0) + t.amount;
  });

  const summary = budgetLimits.map(b => ({
    category_name: b.category_name,
    allocated_limit: b.allocated_limit,
    spent_amount: spentMap[b.category_name] !== undefined ? spentMap[b.category_name] : b.spent_amount
  }));

  res.json(summary);
});

const PORT = 3001;
app.listen(PORT, () => {
  console.log(`LedgerLens server running on port ${PORT}`);
});