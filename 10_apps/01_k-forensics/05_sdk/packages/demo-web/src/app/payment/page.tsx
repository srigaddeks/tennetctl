'use client';

export default function PaymentPage() {
  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: '#0d1b2a' }}>Make a Payment</h1>
        <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: 14 }}>Pay a bill, credit card, or vendor from your checking account</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 24 }}>
        <div style={{ background: '#fff', borderRadius: 12, padding: 32, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
          <form onSubmit={(e) => e.preventDefault()}>
            <div style={{ marginBottom: 20 }}>
              <label htmlFor="pay-from" style={{ display: 'block', marginBottom: 6, fontSize: 13, fontWeight: 600, color: '#334155' }}>Pay From</label>
              <select id="pay-from" style={{ width: '100%', padding: '12px 14px', borderRadius: 8, border: '1px solid #e2e8f0', background: '#f8fafc', color: '#0d1b2a', fontSize: 14, boxSizing: 'border-box' }}>
                <option>Checking ****4832 — $24,832.50</option>
                <option>Savings ****9071 — $156,420.00</option>
              </select>
            </div>

            <div style={{ marginBottom: 20 }}>
              <label htmlFor="payee" style={{ display: 'block', marginBottom: 6, fontSize: 13, fontWeight: 600, color: '#334155' }}>Payee</label>
              <input
                type="text" name="payee" id="payee"
                placeholder="Search payees or enter account number"
                style={{ width: '100%', padding: '12px 14px', borderRadius: 8, border: '1px solid #e2e8f0', background: '#f8fafc', color: '#0d1b2a', fontSize: 14, boxSizing: 'border-box' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
              <div>
                <label htmlFor="amount" style={{ display: 'block', marginBottom: 6, fontSize: 13, fontWeight: 600, color: '#334155' }}>Amount (USD)</label>
                <input
                  type="text" name="amount" id="amount"
                  placeholder="0.00"
                  style={{ width: '100%', padding: '12px 14px', borderRadius: 8, border: '1px solid #e2e8f0', background: '#f8fafc', color: '#0d1b2a', fontSize: 20, fontWeight: 700, boxSizing: 'border-box' }}
                />
              </div>
              <div>
                <label htmlFor="pay-date" style={{ display: 'block', marginBottom: 6, fontSize: 13, fontWeight: 600, color: '#334155' }}>Payment Date</label>
                <input
                  type="date" name="date" id="pay-date"
                  defaultValue="2026-04-10"
                  style={{ width: '100%', padding: '12px 14px', borderRadius: 8, border: '1px solid #e2e8f0', background: '#f8fafc', color: '#0d1b2a', fontSize: 14, boxSizing: 'border-box' }}
                />
              </div>
            </div>

            <div style={{ marginBottom: 24 }}>
              <label htmlFor="memo" style={{ display: 'block', marginBottom: 6, fontSize: 13, fontWeight: 600, color: '#334155' }}>Memo (optional)</label>
              <input
                type="text" name="memo" id="memo"
                placeholder="Invoice number or description"
                style={{ width: '100%', padding: '12px 14px', borderRadius: 8, border: '1px solid #e2e8f0', background: '#f8fafc', color: '#0d1b2a', fontSize: 14, boxSizing: 'border-box' }}
              />
            </div>

            <div style={{ display: 'flex', gap: 12 }}>
              <button
                type="submit"
                data-kp-commit="payment"
                style={{ flex: 1, padding: '14px', borderRadius: 8, border: 'none', background: '#1b998b', color: '#fff', fontSize: 15, fontWeight: 600, cursor: 'pointer' }}
              >
                Confirm Payment
              </button>
              <button
                type="button"
                style={{ padding: '14px 24px', borderRadius: 8, border: '1px solid #e2e8f0', background: '#fff', color: '#64748b', fontSize: 14, cursor: 'pointer' }}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>

        <div>
          <div style={{ background: '#fff', borderRadius: 12, padding: 24, boxShadow: '0 1px 3px rgba(0,0,0,0.08)', marginBottom: 16 }}>
            <h3 style={{ margin: '0 0 16px', fontSize: 14, fontWeight: 600, color: '#334155' }}>Recent Payees</h3>
            {['Comcast Business — $189.99', 'State Farm Insurance — $245.00', 'City Water Utility — $67.50', 'Visa ****7623 — $3,215.80'].map((p, i) => (
              <div key={i} style={{ padding: '10px 0', borderBottom: i < 3 ? '1px solid #f1f5f9' : 'none', fontSize: 13, color: '#475569', cursor: 'pointer' }}>{p}</div>
            ))}
          </div>

          <div style={{ background: '#fef3c7', borderRadius: 12, padding: 16, border: '1px solid #fbbf24' }}>
            <p style={{ margin: 0, fontSize: 12, color: '#92400e', fontWeight: 600 }}>Daily Limit</p>
            <p style={{ margin: '4px 0 0', fontSize: 12, color: '#92400e' }}>$25,000.00 remaining today</p>
          </div>
        </div>
      </div>
    </div>
  );
}
