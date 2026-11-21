# Wave W9 Backend Test & Operational Guide

**Module:** Financial Years & App Releases (What's New)  
**Release:** Wave W9 Backend  

---

## 1. Endpoint Reference & Quick Test Commands

### 1.1 List Financial Years
```http
GET /api/v1/financial-years?page=1&page_size=10
Authorization: Bearer <TOKEN>
```

### 1.2 Get Currently Operating Fiscal Year
```http
GET /api/v1/financial-years/current
Authorization: Bearer <TOKEN>
```

### 1.3 Create New Financial Year
```http
POST /api/v1/financial-years
Authorization: Bearer <TOKEN>
Content-Type: application/json

{
  "name": "FY 2027-2028",
  "code": "2027-2028",
  "start_date": "2027-04-01",
  "end_date": "2028-03-31",
  "is_current": false,
  "is_active": true,
  "description": "Forward outlook fiscal period"
}
```

### 1.4 Set Current Operating Year
```http
POST /api/v1/financial-years/{year_id}/set-current
Authorization: Bearer <TOKEN>
```

### 1.5 List App Releases
```http
GET /api/v1/releases?page=1&page_size=10
Authorization: Bearer <TOKEN>
```

### 1.6 Fetch Latest Release for Modal Announcement
```http
GET /api/v1/releases/latest
Authorization: Bearer <TOKEN>
```
