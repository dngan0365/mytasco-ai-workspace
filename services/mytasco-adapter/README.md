# mytasco-adapter

Thin client SDK gọi COP API của My Tasco (staff directory, org graph, attendance,
requests & approvals, payroll, news, notifications), theo đúng path/param/envelope
mô tả trong **My Tasco AI Hackathon API Documentation**.

Đây là package Python độc lập để mọi service khác trong repo (orchestrator,
ingestion, hoặc script agent riêng) cùng import dùng chung — không phải viết lại
logic gọi API ở nhiều nơi.

## Cài đặt (editable, dùng trong monorepo)

```bash
pip install -e ../mytasco-adapter
```

## Sử dụng

```python
from mytasco_adapter import MyTascoClient

client = MyTascoClient(base_url="http://localhost:8788")  # mặc định đọc env MYTASCO_MOCK_BASE_URL
result = await client.search_staff(keyword="nguyen")
```

## Đổi sang gateway thật (production)

```python
client = MyTascoClient(base_url="https://dev-api-swm.dnpwater.vn/cop")
```

Envelope response (`status/message/body/requestId`) và tên field DTO không đổi,
nên code gọi phía trên không cần sửa gì thêm.
