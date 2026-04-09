from sqlalchemy.orm import declarative_base

# Lớp Base mà tất cả các Model (User, Key, Document) sẽ kế thừa.
# Việc tách ra file riêng giúp tránh lỗi Circular Import (Import vòng tròn)
# khi các model liên kết với nhau.
Base = declarative_base()
