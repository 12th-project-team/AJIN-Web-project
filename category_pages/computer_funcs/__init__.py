# category_pages/computer_funcs/__init__.py

# 하위 모듈의 render 함수만 외부로 노출
from .upload    import render               as upload
from .preview   import render               as preview
from .summary   import render               as summary
from .exam      import render               as exam
from .quiz      import render               as quiz
from .chatbot   import render               as chatbot
