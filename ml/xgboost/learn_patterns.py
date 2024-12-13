import xgboost as xgb
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

from . import settings
from . import utils
# تحميل البيانات
data = pd.read_csv('your_data.csv')

# تقسيم البيانات إلى ميزات وأهداف
X = data[['Open', 'High', 'Low', 'Close', 'Volume']].values
y = data['Target'].values

# تقسيم البيانات إلى مجموعة تدريب واختبار
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# تحويل البيانات إلى DMatrix
dtrain = xgb.DMatrix(X_train, label=y_train)
dtest = xgb.DMatrix(X_test, label=y_test)

# إعداد معلمات النموذج
params = {
    'objective': 'binary:logistic',  # تصنيف ثنائي
    'max_depth': 5,                  # عمق الشجرة
    'learning_rate': 0.1,            # سرعة التعلم
    'eval_metric': 'logloss'         # مقياس التقييم
}

# تدريب النموذج
model = xgb.train(params, dtrain, num_boost_round=100)

# التنبؤ بالنتائج
y_pred = model.predict(dtest)

# تحويل التنبؤات إلى فئات (0 أو 1)
y_pred_binary = (y_pred > 0.5).astype(int)

# تقييم النموذج
accuracy = accuracy_score(y_test, y_pred_binary)
print(f"Accuracy: {accuracy * 100:.2f}%")
