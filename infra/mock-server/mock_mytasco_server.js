// Mock My Tasco COP API server
// Usage: node mock_mytasco_server.js   (listens on :8788)
// Requires: npm install express  (run once in this folder)

const express = require('express');
const { randomUUID } = require('crypto');

const app = express();
app.use(express.json());

// ---------- helpers ----------
function envelope(body, req) {
  return {
    status: 'success',
    message: 'SUCCESS',
    body,
    requestId: req.header('X-Request-Id') || randomUUID(),
  };
}

function errorEnvelope(res, httpCode, code, message) {
  res.status(httpCode).json({
    status: 'error',
    code,
    message,
    technicalMessage: message,
    requestId: randomUUID(),
  });
}

function paginate(arr, pageInfo = {}) {
  const pageSize = pageInfo.pageSize || 20;
  const currentPage = pageInfo.currentPage || 0;
  const start = currentPage * pageSize;
  return {
    result: arr.slice(start, start + pageSize),
    pageInfo: { pageSize, currentPage, totalRecord: arr.length },
  };
}

// ---------- sample data ----------
const staffData = [
  { staffId: 10472, staffCode: 'NS-10472', staffName: 'Nguyen Van A', title: 'Field Technician', email: 'a.nguyen@dnpwater.vn', phoneNumber: '0901234567', status: 1, provinceName: 'Ha Noi', listOrgUnit: [{ orgUnitId: 32, orgUnitCode: 'PB-KT', orgUnitName: 'Phong Ky Thuat' }] },
  { staffId: 10001, staffCode: 'NS-10001', staffName: 'Tran Thi B', title: 'Team Manager', email: 'b.tran@dnpwater.vn', phoneNumber: '0902345678', status: 1, provinceName: 'Ho Chi Minh', listOrgUnit: [{ orgUnitId: 32, orgUnitCode: 'PB-KT', orgUnitName: 'Phong Ky Thuat' }] },
  { staffId: 10555, staffCode: 'NS-10555', staffName: 'Le Van C', title: 'HR Executive', email: 'c.le@dnpwater.vn', phoneNumber: '0903456789', status: 1, provinceName: 'Ha Noi', listOrgUnit: [{ orgUnitId: 40, orgUnitCode: 'PB-NS', orgUnitName: 'Phong Nhan Su' }] },
];

const orgTree = [
  {
    organizationId: 1, organizationName: 'DNP Water', organizationCode: 'DNP', parentId: null,
    children: [
      { organizationId: 32, organizationName: 'Phong Ky Thuat', parentId: 1, children: [] },
      { organizationId: 40, organizationName: 'Phong Nhan Su', parentId: 1, children: [] },
    ],
  },
];

const requests = [
  { id: 5012, requestType: 'LEAVE', status: 'PENDING', staffId: 10472, fromDate: '2026-07-01', toDate: '2026-07-03', reason: 'Annual leave', currentApprover: 'NS-10001' },
  { id: 5013, requestType: 'OVERTIME', status: 'APPROVED', staffId: 10472, fromDate: '2026-06-20', toDate: '2026-06-20', reason: 'Project deadline', currentApprover: 'NS-10001' },
];

const news = [
  { id: 880, title: 'Safety guidelines Q3', categoryName: 'HSE', status: 'PUBLISHED', publishedAt: '2026-06-20T03:00:00Z', reactionCount: 42, summary: 'Updated field-work safety rules effective July.' },
  { id: 881, title: 'Company town hall recap', categoryName: 'General', status: 'PUBLISHED', publishedAt: '2026-06-25T03:00:00Z', reactionCount: 18, summary: 'Highlights from the Q2 town hall meeting.' },
];

const notifications = [
  { id: 99312, title: 'Request approved', body: 'Your leave request #5012 was approved.', type: 'REQUEST', isRead: false, createdAt: '2026-06-26T01:10:00Z', refId: 5012 },
  { id: 99313, title: 'New safety policy', body: 'Please review the updated HSE guidelines.', type: 'NEWS', isRead: true, createdAt: '2026-06-20T04:00:00Z', refId: 880 },
];

// ---------- health ----------
app.get('/health', (req, res) => res.json({ status: 'ok' }));

// ---------- 1. Staff directory ----------
function staffSearchHandler(req, res) {
  const { keyword, orgUnitId, status } = req.body?.example || {};
  let list = staffData;
  if (keyword) list = list.filter(s => s.staffName.toLowerCase().includes(keyword.toLowerCase()) || s.staffCode.toLowerCase().includes(keyword.toLowerCase()));
  if (orgUnitId) list = list.filter(s => s.listOrgUnit.some(o => o.orgUnitId === orgUnitId));
  if (status !== undefined) list = list.filter(s => s.status === status);
  res.json(envelope(paginate(list, req.body?.pageInfo), req));
}
app.post('/staff/search', staffSearchHandler);
app.post('/staff/quick-search', staffSearchHandler);

// ---------- 2. AI usage overview ----------
app.get('/ai-usage-overview/general', (req, res) => {
  res.json(envelope({
    general: { totalCost: 184.52, percentageChangeTotalCost: 12.4, totalQuestion: 8421, percentageChangeTotalQuestion: 9.1, totalUser: 312, totalToken: 5120340, percentError: 1.8, avgMillis: 2400 },
    usageTrends: [{ usageTime: '2026-06-25', totalQuestion: 410 }, { usageTime: '2026-06-26', totalQuestion: 455 }],
    costTrends: [{ usageDate: '2026-06-25', totalCost: 9.12 }, { usageDate: '2026-06-26', totalCost: 10.03 }],
    rankByOrganizationLv1: [{ organizationName: 'Phong Ky Thuat', totalQuestion: 3120 }, { organizationName: 'Phong Nhan Su', totalQuestion: 1890 }],
  }, req));
});

// ---------- 3. Organization graph ----------
app.get('/organization/tree', (req, res) => res.json(envelope({ result: orgTree }, req)));
app.get('/staff-org/by-current-staff', (req, res) => res.json(envelope({ result: orgTree[0].children }, req)));
app.get('/orgUnit/initTree', (req, res) => res.json(envelope({ result: orgTree }, req)));

// ---------- 4. Attendance ----------
function attendanceRow(date) {
  return { date, checkIn: '08:02', checkOut: '17:35', workingHours: 8.5, status: 'on_time', location: 'HQ Ha Noi' };
}
app.get('/attendance/by-staff', (req, res) => {
  res.json(envelope({
    result: [attendanceRow('2026-06-25'), attendanceRow('2026-06-26')],
    summary: { workingDays: 21, lateDays: 2, absentDays: 0 },
  }, req));
});
app.get('/attendance/summary-by-staff', (req, res) => res.json(envelope({ summary: { workingDays: 21, lateDays: 2, absentDays: 0 } }, req)));
app.post('/attendance/search', (req, res) => res.json(envelope(paginate([attendanceRow('2026-06-25'), attendanceRow('2026-06-26')], req.body?.pageInfo), req)));
app.get('/attendance-entry/self-list', (req, res) => res.json(envelope({ result: [attendanceRow(req.query.date || '2026-06-26')] }, req)));

// ---------- 5. Requests & approvals ----------
app.post('/request/search', (req, res) => {
  const { status, requestType } = req.body?.example || {};
  let list = requests;
  if (status) list = list.filter(r => r.status === status);
  if (requestType) list = list.filter(r => r.requestType === requestType);
  res.json(envelope(paginate(list, req.body?.pageInfo), req));
});
app.post('/request/create', (req, res) => {
  const newReq = { id: 5000 + requests.length + 1, status: 'PENDING', ...req.body };
  requests.push(newReq);
  res.json(envelope({ result: newReq }, req));
});
app.get('/request/self', (req, res) => {
  const found = requests.find(r => r.id === Number(req.query.id));
  if (!found) return errorEnvelope(res, 404, 'not_found', 'request not found');
  res.json(envelope({ result: found }, req));
});
function setStatus(newStatus) {
  return (req, res) => {
    const found = requests.find(r => r.id === Number(req.body.id));
    if (!found) return errorEnvelope(res, 404, 'not_found', 'request not found');
    found.status = newStatus;
    res.json(envelope({ result: found }, req));
  };
}
app.post('/request/approve', setStatus('APPROVED'));
app.post('/request/reject', setStatus('REJECTED'));
app.post('/request/cancel', setStatus('CANCELLED'));
app.get('/request/count', (req, res) => res.json(envelope({ pending: requests.filter(r => r.status === 'PENDING').length }, req)));

// ---------- 6. Payroll (OTP gated) ----------
function requireOtp(req, res) {
  if (!req.query.otp && !req.query.otpTransactionId) {
    errorEnvelope(res, 403, 'forbidden', 'OTP step-up verification required');
    return false;
  }
  return true;
}
app.get('/salary-staff-payslip/self-by-month', (req, res) => {
  if (!requireOtp(req, res)) return;
  res.json(envelope({
    month: Number(req.query.month) || 6, year: Number(req.query.year) || 2026,
    grossIncome: 18500000, netIncome: 16320000,
    items: [
      { code: 'BASE', name: 'Base salary', amount: 15000000 },
      { code: 'OT', name: 'Overtime', amount: 1200000 },
      { code: 'INS', name: 'Insurance', amount: -1080000 },
    ],
  }, req));
});
app.get('/salary-staff/self-by-month', (req, res) => {
  if (!requireOtp(req, res)) return;
  res.json(envelope({ month: Number(req.query.month) || 6, year: Number(req.query.year) || 2026, netIncome: 16320000 }, req));
});
app.get('/salary-staff/stats-month', (req, res) => {
  if (!requireOtp(req, res)) return;
  res.json(envelope({ series: [{ month: 4, netIncome: 15900000 }, { month: 5, netIncome: 16100000 }, { month: 6, netIncome: 16320000 }] }, req));
});
app.get('/salary-staff-payslip/self-by-year', (req, res) => {
  if (!requireOtp(req, res)) return;
  res.json(envelope({ year: Number(req.query.year) || 2026, totalGross: 111000000, totalNet: 98000000 }, req));
});

// ---------- 7. News & feed ----------
app.get('/news-article/search', (req, res) => {
  const { keyword, categoryId } = req.query;
  let list = news;
  if (keyword) list = list.filter(n => n.title.toLowerCase().includes(String(keyword).toLowerCase()));
  if (categoryId) list = list.filter(n => n.categoryName);
  res.json(envelope(paginate(list, { pageSize: Number(req.query.pageSize) || 10, currentPage: Number(req.query.page) || 0 }), req));
});
app.get('/news-article/latest', (req, res) => res.json(envelope({ result: news.slice(0, 5) }, req)));
app.get('/news-article/self', (req, res) => {
  const found = news.find(n => n.id === Number(req.query.id));
  if (!found) return errorEnvelope(res, 404, 'not_found', 'article not found');
  res.json(envelope({ result: found }, req));
});
app.get('/news-category/search', (req, res) => res.json(envelope({ result: [{ categoryId: 4, categoryName: 'HSE' }, { categoryId: 1, categoryName: 'General' }] }, req)));
app.post('/news-article/react', (req, res) => res.json(envelope({ ok: true }, req)));
app.get('/banner/visible', (req, res) => res.json(envelope({ result: [] }, req)));

// ---------- 8. Notifications ----------
app.get('/noti-app/search', (req, res) => {
  const { isRead } = req.query;
  let list = notifications;
  if (isRead !== undefined) list = list.filter(n => String(n.isRead) === isRead);
  res.json(envelope(paginate(list, { pageSize: Number(req.query.pageSize) || 20, currentPage: Number(req.query.currentPage) || 0 }), req));
});
app.get('/noti-app/count-unread', (req, res) => res.json(envelope({ unread: notifications.filter(n => !n.isRead).length }, req)));
app.post('/noti-app/mark-read', (req, res) => {
  const found = notifications.find(n => n.id === Number(req.body.id));
  if (!found) return errorEnvelope(res, 404, 'not_found', 'notification not found');
  found.isRead = true;
  res.json(envelope({ result: found }, req));
});

// ---------- 404 fallback ----------
app.use((req, res) => errorEnvelope(res, 404, 'not_found', `no mock handler for ${req.method} ${req.path}`));

const PORT = 8788;
app.listen(PORT, () => console.log(`Mock My Tasco COP server listening on http://localhost:${PORT}`));
