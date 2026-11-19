# eFHUB Scraper — GitHub Actions

هذه هي بنية البداية لنقل مشروع Colab إلى GitHub Actions. لا ترفع أي مفاتيح أو كلمات مرور إلى GitHub.

## الملفات
- `src/efhub_pipeline/config.py`: قراءة الإعدادات والأسرار من Environment Variables.
- `src/efhub_pipeline/pipeline.py`: مكان نقل مراحل Notebook إليه بعد إزالة أوامر Colab.
- `src/efhub_pipeline/__main__.py`: نقطة تشغيل البرنامج.
- `.github/workflows/scrape.yml`: تشغيل يدوي أو مجدول.
- `requirements.txt`: مكتبات Python.

## إعداد GitHub
1. ارفع محتويات هذا المجلد إلى جذر المستودع `Erorr777/efhub-scraper`.
2. افتح Settings → Secrets and variables → Actions → New repository secret.
3. أضف الأسرار التالية من حساباتك بعد تدوير المفاتيح التي ظهرت سابقًا في ملف Notebook:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `R2_ACCOUNT_ID`
   - `R2_ACCESS_KEY_ID`
   - `R2_SECRET_ACCESS_KEY`
   - `R2_BUCKET_NAME`
   - `R2_PUBLIC_URL`
4. افتح Actions → eFHUB Scraper → Run workflow للتشغيل اليدوي.

## تنبيه مهم
الملفات الحالية هي هيكل تشغيل آمن وليست نقلًا مكتملًا للـ Notebook بعد. يجب نقل منطق الخلايا الخمس إلى `pipeline.py` مع إزالة:
- `from google.colab import drive` و `drive.mount(...)`
- أوامر `!pip` و `!playwright install...` (التثبيت أصبح في workflow)
- مسارات `/content/...` واستبدالها بمجلد `data/` أو `artifacts/`
- القيم السرية المكتوبة مباشرة في الكود واستبدالها بـ `config.py`

لا تفعل تشغيلًا مجدولًا قبل اختبار تشغيل يدوي محدود (`MAX_PAGES=3`).
