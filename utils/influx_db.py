from influxdb import InfluxDBClient as BaseClient
from typing import List,Dict


class InfluxClient(BaseClient):
    def __init__(self,db_name,host='localhost',port=8086,logger=None):
        # type:(str,str,int,Logger) -> None
        BaseClient.__init__(self,host=host,port=port,database=db_name)
        if logger:
            self.__log_info = logger.info
            self.__log_error = logger.error
        else:
            from utils.log_config import Logger, log_info, log_error
            self.__log_info = log_info
            self.__log_error = log_error
    def query_series(self,measurement,show_fts=None,filters=None,st_timestamp=0,ed_timestamp=0):
        # type:(str,List,Dict,int,int) -> (List,List[List],str)
        try:
            sql = "SELECT "
            if show_fts:
                sql += ','.join(['"{}"'.format(i) for i in show_fts]) + ' '
            else:
                sql += '* '
            sql += 'FROM {} '.format(measurement)
            qs = []
            if filters:
                for k in filters:
                    v = filters[k]
                    if isinstance(v, str):
                        qs.append(' "{}"=\'{}\' '.format(k, v))
                    else:
                        qs.append(' "{}"={} '.format(k, v))
            if st_timestamp:
                qs.append(' "time">={} '.format(int(st_timestamp*1000000000)))
            if ed_timestamp:
                qs.append(' "time"<{} '.format(int(ed_timestamp * 1000000000)))
            if qs:
                sql += 'WHERE ' + 'AND'.join(qs)
            sql += ';'
            self.__log_info("[InfluxClient] [sql]={}".format(sql))
            res = self.query(sql,params={'epoch':'s'}).raw.get('series')
            if res:
                return res[0]['columns'],res[0]['values'],''
            else:
                return [],[],''
        except Exception as e:
            return [],[],'{}'.format(e)
    def add_point(self,measurement, fields, timestamp, tags=None):
        # type:(str,dict,int,dict) -> str
        try:
            data = {
                "measurement": measurement,
                "time": timestamp,
                "fields": fields,
            }
            if tags:
                data['tags'] = tags
            self.write_points([data], time_precision='s')
            return ''
        except Exception as e:
            return '{}'.format(e)
    def get_latest_points(self,measurement, N, show_fts=None, filters=None):
        # type:(str,int,List,Dict) -> (List,List[List])
        try:
            sql = "SELECT "
            if show_fts:
                sql += ','.join(['"{}"'.format(i) for i in show_fts]) + ' '
            else:
                sql += '* '
            sql += 'FROM {} '.format(measurement)
            if filters:
                qs = []
                for k in filters:
                    v = filters[k]
                    if isinstance(v, str):
                        qs.append(' "{}"=\'{}\' '.format(k, v))
                    else:
                        qs.append(' "{}"={} '.format(k, v))
                sql += 'WHERE ' + 'AND'.join(qs)
            sql += ' ORDER BY time DESC LIMIT {};'.format(N)
            self.__log_info("[InfluxClient] [sql]={}".format(sql))
            res = self.query(sql, params={'epoch': 's'}).raw.get('series')
            if res:
                return res[0]['columns'], res[0]['values'],''
            else:
                return [], [],''
        except Exception as e:
            return [],[],'{}'.format(e)




#### test ####
if __name__ == '__main__':
    measurement = 'cpu_load_short'
    cli = InfluxClient('mydb')
