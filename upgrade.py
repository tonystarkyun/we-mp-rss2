import os
import yaml
import tempfile
import sys
from alembic.config import Config
from alembic import command
from core.config import cfg
class DatabaseUpgrader:
    def __init__(self, config_path="alembic.ini", yaml_config_path=None):
        """
        初始化数据库升级器
        :param config_path: alembic配置文件路径
        :param yaml_config_path: yaml配置文件路径
        """
        if yaml_config_path:
            config=cfg._config 
            # 创建临时alembic.ini文件
            temp_ini = tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False)
            temp_ini.write(f"""
                            [alembic]
                            sqlalchemy.url = {config.get('db')}

                            [loggers]
                            keys = root,sqlalchemy,alembic

                            [handlers]
                            keys = console

                            [formatters]
                            keys = generic

                            [logger_root]
                            level = WARN
                            handlers = console
                            qualname =

                            [logger_sqlalchemy]
                            level = WARN
                            handlers =
                            qualname = sqlalchemy.engine

                            [logger_alembic]
                            level = INFO
                            handlers =
                            qualname = alembic

                            [handler_console]
                            class = StreamHandler
                            args = (sys.stderr,)
                            level = NOTSET
                            formatter = generic

                            [formatter_generic]
                            format = %(levelname)-5.5s [%(name)s] %(message)s
                            datefmt = %H:%M:%S
                            """)
            temp_ini.close()
            config_path = temp_ini.name
            self._temp_config_path = config_path  # 保存临时文件路径以便后续清理
            
        self.alembic_cfg = Config(config_path)
    
    def upgrade_database(self):
        """执行数据库升级到最新版本"""
        try:
            command.upgrade(self.alembic_cfg, "head")
            print("数据库表结构升级完成")
        finally:
            if hasattr(self, '_temp_config_path') and os.path.exists(self._temp_config_path):
                os.unlink(self._temp_config_path)
    
    def generate_migration(self, message=None):
        """
        自动生成迁移脚本
        :param message: 可选的迁移信息描述
        """
        command.revision(self.alembic_cfg, autogenerate=True, message=message)
        print("迁移脚本生成完成")

if __name__ == "__main__":
    # 创建升级器实例并执行默认操作
    upgrader = DatabaseUpgrader(yaml_config_path="config.yaml")  # 假设配置文件名为config.yaml
    # upgrader.upgrade_database()
    # 如需生成迁移脚本，可取消下面注释
    upgrader.generate_migration("your migration message here")