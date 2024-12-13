import xgboost as xgb
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# تحميل البيانات - استبدل هذا بجداول البيانات الخاصة بك
# تأكد من تنظيف البيانات ومعالجتها قبل التدريب
data = pd.read_csv('your_dataset.csv')

# تقسيم الميزات والمخرجات
X = data.drop(columns=['target'])  # استبدل 'target' بالعمود المستهدف
y = data['target']

# تقسيم البيانات إلى تدريب واختبار
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# تحويل البيانات إلى تنسيق DMatrix لـ XGBoost
dtrain = xgb.DMatrix(X_train, label=y_train)
dtest = xgb.DMatrix(X_test, label=y_test)

# ضبط المعلمات لتحسين اليقين وتقليل Overfitting
params = {
    'objective': 'binary:logistic',  # تصنيف ثنائي
    'max_depth': 5,                  # الحد من عمق الشجرة لتقليل التعقيد
    'learning_rate': 0.01,           # تقليل سرعة التعلم لتحقيق استقرار أفضل
    'n_estimators': 1000,            # عدد الأشجار
    'subsample': 0.8,                # اختيار نسبة بيانات عشوائية لتقليل Overfitting
    'colsample_bytree': 0.8,         # اختيار نسبة الميزات العشوائية لكل شجرة
    'lambda': 1,                     # الانتظام L2
    'alpha': 0.5,                    # الانتظام L1
    'eval_metric': 'logloss',        # مقياس التقييم
}

# تدريب النموذج باستخدام البيانات
model = xgb.train(params, dtrain, num_boost_round=300, evals=[(dtest, 'test')], early_stopping_rounds=50)

# توقع المخرجات باستخدام بيانات الاختبار
y_pred_prob = model.predict(dtest)
y_pred = [1 if prob >= 0.5 else 0 for prob in y_pred_prob]  # تحويل الاحتمالات إلى تصنيفات

# تقييم الأداء
accuracy = accuracy_score(y_test, y_pred)
print("دقة النموذج:", accuracy)
print("\nتقرير التصنيف:\n", classification_report(y_test, y_pred))

# إذا كنت بحاجة إلى زيادة اليقين إلى 95%:
if accuracy < 0.95:
    print("النموذج يحتاج إلى تحسين إضافي.")
else:
    print("النموذج يحقق مستوى الدقة المطلوب.")
