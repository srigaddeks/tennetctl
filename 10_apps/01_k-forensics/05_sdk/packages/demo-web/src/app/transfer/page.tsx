'use client';

export default function TransferPage() {
  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: '#0d1b2a' }}>Wire Transfer</h1>
        <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: 14 }}>Send a domestic or international wire transfer</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 24 }}>
        <div style={{ background: '#fff', borderRadius: 12, padding: 32, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
          <form onSubmit={(e) => e.preventDefault()}>
            <div style={{ background: '#fef2f2', borderRadius: 8, padding: 12, marginBottom: 24, border: '1px solid #fecaca' }}>
              <p style={{ margin: 0, fontSize: 12, color: '#991b1b', fontWeight: 600 }}>Important: Wire transfers are final and cannot be reversed. Please verify all details carefully.</p>
            </div>

            <h3 style={{ margin: '0 0 16px', fontSize: 14, fontWeight: 600, color: '#334155', textTransform: 'uppercase' as const, letterSpacing: 0.5 }}>Sender</h3>
            <div style={{ marginBottom: 20 }}>
              <label htmlFor="from-account" style={{ display: 'block', marginBottom: 6, fontSize: 13, fontWeight: 600, color: '#334155' }}>From Account</label>
              <select id="from-account" style={{ width: '100%', padding: '12px 14px', borderRadius: 8, border: '1px solid #e2e8f0', background: '#f8fafc', color: '#0d1b2a', fontSize: 14, boxSizing: 'border-box' }}>
                <option>Checking ****4832 — Available: $24,832.50</option>
                <option>Savings ****9071 — Available: $156,420.00</option>
              </select>
            </div>

            <h3 style={{ margin: '0 0 16px', fontSize: 14, fontWeight: 600, color: '#334155', textTransform: 'uppercase' as const, letterSpacing: 0.5 }}>Recipient</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
              <div>
                <label htmlFor="recipient-name" style={{ display: 'block', marginBottom: 6, fontSize: 13, fontWeight: 600, color: '#334155' }}>Beneficiary Name</label>
                <input type="text" name="recipient-name" id="recipient-name" placeholder="Full legal name"
                  style={{ width: '100%', padding: '12px 14px', borderRadius: 8, border: '1px solid #e2e8f0', background: '#f8fafc', color: '#0d1b2a', fontSize: 14, boxSizing: 'border-box' }} />
              </div>
              <div>
                <label htmlFor="bank-name" style={{ display: 'block', marginBottom: 6, fontSize: 13, fontWeight: 600, color: '#334155' }}>Bank Name</label>
                <input type="text" name="bank-name" id="bank-name" placeholder="Receiving bank"
                  style={{ width: '100%', padding: '12px 14px', borderRadius: 8, border: '1px solid #e2e8f0', background: '#f8fafc', color: '#0d1b2a', fontSize: 14, boxSizing: 'border-box' }} />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
              <div>
                <label htmlFor="routing" style={{ display: 'block', marginBottom: 6, fontSize: 13, fontWeight: 600, color: '#334155' }}>Routing / SWIFT</label>
                <input type="text" name="routing" id="routing" placeholder="021000021 or BOFAUS3N"
                  style={{ width: '100%', padding: '12px 14px', borderRadius: 8, border: '1px solid #e2e8f0', background: '#f8fafc', color: '#0d1b2a', fontSize: 14, boxSizing: 'border-box' }} />
              </div>
              <div>
                <label htmlFor="account-number" style={{ display: 'block', marginBottom: 6, fontSize: 13, fontWeight: 600, color: '#334155' }}>Account Number</label>
                <input type="text" name="account-number" id="account-number" placeholder="Beneficiary account"
                  style={{ width: '100%', padding: '12px 14px', borderRadius: 8, border: '1px solid #e2e8f0', background: '#f8fafc', color: '#0d1b2a', fontSize: 14, boxSizing: 'border-box' }} />
              </div>
            </div>

            <h3 style={{ margin: '0 0 16px', fontSize: 14, fontWeight: 600, color: '#334155', textTransform: 'uppercase' as const, letterSpacing: 0.5 }}>Transfer Details</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
              <div>
                <label htmlFor="wire-amount" style={{ display: 'block', marginBottom: 6, fontSize: 13, fontWeight: 600, color: '#334155' }}>Amount (USD)</label>
                <input type="text" name="amount" id="wire-amount" placeholder="0.00"
                  style={{ width: '100%', padding: '12px 14px', borderRadius: 8, border: '1px solid #e2e8f0', background: '#f8fafc', color: '#0d1b2a', fontSize: 20, fontWeight: 700, boxSizing: 'border-box' }} />
              </div>
              <div>
                <label htmlFor="purpose" style={{ display: 'block', marginBottom: 6, fontSize: 13, fontWeight: 600, color: '#334155' }}>Purpose</label>
                <select id="purpose" style={{ width: '100%', padding: '12px 14px', borderRadius: 8, border: '1px solid #e2e8f0', background: '#f8fafc', color: '#0d1b2a', fontSize: 14, boxSizing: 'border-box' }}>
                  <option>Business payment</option>
                  <option>Personal transfer</option>
                  <option>Real estate closing</option>
                  <option>Investment</option>
                  <option>Other</option>
                </select>
              </div>
            </div>

            <div style={{ marginBottom: 24 }}>
              <label htmlFor="reference" style={{ display: 'block', marginBottom: 6, fontSize: 13, fontWeight: 600, color: '#334155' }}>Reference / Memo</label>
              <input type="text" name="reference" id="reference" placeholder="Invoice number or description"
                style={{ width: '100%', padding: '12px 14px', borderRadius: 8, border: '1px solid #e2e8f0', background: '#f8fafc', color: '#0d1b2a', fontSize: 14, boxSizing: 'border-box' }} />
            </div>

            <div style={{ display: 'flex', gap: 12 }}>
              <button type="submit" data-kp-commit="transfer"
                style={{ flex: 1, padding: '14px', borderRadius: 8, border: 'none', background: '#dc2626', color: '#fff', fontSize: 15, fontWeight: 600, cursor: 'pointer' }}>
                Send Wire Transfer
              </button>
              <button type="button"
                style={{ padding: '14px 24px', borderRadius: 8, border: '1px solid #e2e8f0', background: '#fff', color: '#64748b', fontSize: 14, cursor: 'pointer' }}>
                Cancel
              </button>
            </div>
          </form>
        </div>

        <div>
          <div style={{ background: '#fff', borderRadius: 12, padding: 24, boxShadow: '0 1px 3px rgba(0,0,0,0.08)', marginBottom: 16 }}>
            <h3 style={{ margin: '0 0 12px', fontSize: 14, fontWeight: 600, color: '#334155' }}>Wire Fee</h3>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ fontSize: 13, color: '#64748b' }}>Domestic wire</span>
              <span style={{ fontSize: 13, fontWeight: 600, color: '#0d1b2a' }}>$25.00</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 13, color: '#64748b' }}>International wire</span>
              <span style={{ fontSize: 13, fontWeight: 600, color: '#0d1b2a' }}>$45.00</span>
            </div>
          </div>

          <div style={{ background: '#fff', borderRadius: 12, padding: 24, boxShadow: '0 1px 3px rgba(0,0,0,0.08)', marginBottom: 16 }}>
            <h3 style={{ margin: '0 0 12px', fontSize: 14, fontWeight: 600, color: '#334155' }}>Processing Time</h3>
            <p style={{ margin: 0, fontSize: 13, color: '#64748b' }}>Domestic: Same business day if submitted before 4:00 PM ET</p>
            <p style={{ margin: '8px 0 0', fontSize: 13, color: '#64748b' }}>International: 1-3 business days</p>
          </div>

          <div style={{ background: '#fef3c7', borderRadius: 12, padding: 16, border: '1px solid #fbbf24' }}>
            <p style={{ margin: 0, fontSize: 12, color: '#92400e', fontWeight: 600 }}>Wire Limit: $100,000/day</p>
            <p style={{ margin: '4px 0 0', fontSize: 12, color: '#92400e' }}>$100,000.00 remaining today</p>
          </div>
        </div>
      </div>
    </div>
  );
}
