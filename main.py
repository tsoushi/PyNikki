import sqlite3
import logging

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    LOGLEVEL = logging.INFO

    logger.setLevel(LOGLEVEL)
    streamHandler = logging.StreamHandler()
    streamHandler.setLevel(LOGLEVEL)
    streamHandler.setFormatter(logging.Formatter('%(levelname)s : %(message)s'))
    logger.addHandler(streamHandler)

SCHEMA_PATH = 'schema.sql'

def get_db():
    return sqlite3.connect('nikki.sqlite3')

def add_comment(comment, groupe=None):
    logger.info('writing to database')
    db = None
    try:
        db = get_db()
        db.execute('INSERT INTO nikki(comment, groupe) VALUES(?, ?);', (comment, groupe))
        db.commit()
        logger.info('writing is complete')
    except sqlite3.OperationalError:
        logger.error('failed to write to database')
        raise
    finally:
        if db:
            db.close()

def init_db():
    logger.info('initializing the database')
    db = None
    try:
        db = get_db()
        with open(SCHEMA_PATH, mode='r', encoding='utf-8') as schema_file:
            db.executescript(schema_file.read())
        db.commit()
        logger.info('initialization is complete')
    except sqlite3.OperationalError:
        logger.error('failed to initialize the database')
        raise
    except FileNotFoundError:
        logger.error('schema file was not found')
        raise
    finally:
        if db:
            db.close()

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 1:
        logger.debug('start in standard input mode')
        groupe = input('グループ: ')
        if groupe == '':
            logger.debug('replace groupe name with None because groupe name is empty')
            groupe = None
        comment = input('コメント: ')
        if comment:
            add_comment(comment, groupe=groupe)

    elif len(sys.argv) == 2:
        if sys.argv[1] == 'initdb':
            init_db()
        else:
            logger.debug('start in argument input mode (groupe name is None)')
            add_comment(sys.argv[1])

    elif len(sys.argv) == 3:
        logger.debug('start in argument input mode')
        add_comment(sys.argv[2], groupe=sys.argv[1])

