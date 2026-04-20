# TennetCTL Dev Credentials

## Server Status
- **Backend**: http://localhost:51734
- **Frontend**: http://localhost:51735
- **Health API**: http://localhost:51734/health
- **Mode**: Single-tenant (TENNETCTL_SINGLE_TENANT=true)

## Initial Setup
On first load, the frontend will prompt for **first admin user creation** (setup wizard).

1. Navigate to http://localhost:51735
2. Complete the setup flow (email + password)
3. Save credentials below after creation

## Test Credentials (after setup)
```
Email: [Set during setup wizard]
Password: [Set during setup wizard]
```

## Modules Enabled
- core
- iam
- audit
- featureflags
- vault
- notify
- monitoring

**Product_ops removed** as of 2026-04-20 scope cleanup.

## Database
- **URL**: postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl
- **User**: tennetctl
- **Password**: tennetctl_dev

## Vault Root Key
```
TENNETCTL_VAULT_ROOT_KEY=Gjpz8p/6Zy48sIkudpnebaGgvGH7vhJuGyeh06IHPk0=
```

## Next Steps
1. Complete setup wizard in browser
2. Log in with created credentials
3. Navigate to /system/health to see module status
4. Explore features: /iam, /audit, /vault, /notify, /monitoring, /feature-flags

---
**Notes**: Update this file with actual credentials once setup is complete.
