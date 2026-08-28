طريقة التشغيل:

1) ثبت Python 3.11 أو أحدث.
2) افتح Terminal داخل مجلد المشروع.
3) نفذ:
   pip install -r requirements.txt
4) انسخ .env.example إلى .env
5) ضع توكن البوت في:
   TOKEN=...
6) شغل:
   python main.py

صلاحيات البوت المطلوبة:
- Manage Roles
- Manage Channels (لإنشاء Threads حسب إعدادات السيرفر)
- Send Messages
- Read Message History
- Manage Messages
- Embed Links
- Mention Everyone إذا كنت تريد @here يعمل
- View Channels

من Developer Portal:
- فعّل SERVER MEMBERS INTENT
- فعّل MESSAGE CONTENT INTENT

ملاحظة:
الأمرين /أعطاء_رتب و /ازالة_رتب فيهما 21 خيارًا: عضو + 20 رتبة، لذلك ضمن حد Discord البالغ 25 خيارًا.

غيّر الآيديات أو الصلاحيات في utils/config.py إذا احتجت.
