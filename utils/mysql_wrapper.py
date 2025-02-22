import pymysql
pymysql.install_as_MySQLdb()
from utils.log_config import log_info
from utils.log_config import log_error
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy import BigInteger, BIGINT, Text, Date, DateTime, SmallInteger, String, Integer,CHAR,Float
#
# class MysqlSafeCursor:
#     def __init__(self,conn = None,retry=2):
#         if conn == None:
#             self.__conn = pymysql.Connect(host='localhost',port=3306,user='root',passwd='enter@m_9976',db='my',charset='utf8')
#             self.__need_close_conn = True
#         else:
#             self.__conn = conn
#             self.__need_close_conn = False
#         self.__cursor = self.__conn.cursor()
#         self.__retry = retry
#
#     def __del__(self):
#         try:
#             self.__cursor.close()
#             if self.__need_close_conn:
#                 self.__conn.close()
#         except:
#             log_error("Del MysqlSafeCursor error")
#     def execute(self,sql):
#         tBeg = int(time.time()*1000)
#         ret = False
#         for i in range(0,self.__retry):
#             try:
#                 self.__cursor.execute(sql)
#                 self.__conn.commit()
#                 ret = True
#                 break
#             except:
#                 try:
#                     self.__conn.connect()
#                     self.__cursor = self.__conn.cursor()
#                 except:
#                     log_error("[SQL ERROR] %s"%(sql))
#         log_info("[SQL EXEC] %s time: %dms"%(sql,int(time.time()*1000)-tBeg))
#         return ret
#     def fetchone(self):
#         try:
#             return self.__cursor.fetchone()
#         except:
#             return None
#     def fetchall(self):
#         try:
#             return self.__cursor.fetchall()
#         except:
#             return None

def _create_engine(user, password, host, port, db, autocommit=False, pool_recycle=60, charset='utf8'):
    engine = create_engine('mysql://%s:%s@%s:%s/%s?charset=%s&use_unicode=1' % (user, password, host, port, db, charset),
                           pool_size=10,
                           max_overflow=-1,
                           pool_recycle=pool_recycle,
                           connect_args={'connect_timeout': 3,
                                         'autocommit': 1 if autocommit else 0} )
    return engine

def create_db_scoped_session():
    _engine = _create_engine("root", "enter@m_9976", "localhost", 3306, "my")
    session = scoped_session(sessionmaker())
    session.configure(bind=_engine, autocommit=False,
                      autoflush=False, expire_on_commit=False)
    return session

DbSession = create_db_scoped_session()
# 创建对象的基类:
Base = declarative_base()

def update_write_db(w_session):
    ok,err_msg = True,""
    try:
        w_session.commit()
    except Exception as e:
        err_msg = "{}".format(e)
        ok = False
        w_session.rollback()
    finally:
        w_session.close()
    return ok,err_msg

#定义映射关系
class Kline(Base):
    __tablename__ = 'Kline'
    id = Column(Integer,primary_key=True)
    type = Column(CHAR,primary_key=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    amount = Column(Float)
    period = Column(CHAR,primary_key=True)
    commit = Column(Text)

class Test(Base):
    __tablename__ = 'Test'
    id = Column(Integer, primary_key=True)
    commit = Column(Text)


session = DbSession()
# #写
# kl = Kline()
# kl.id = 456
# kl.type = "usdt"
# kl.open = 100000.3
# kl.period = '1min'
# session.add(kl)
# session.commit()
#
# #读
#result = session.query(Kline).order_by(Kline.id.desc()).limit(1).all()

res = session.query(Test).filter(Test.id==1).all()