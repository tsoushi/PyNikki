import tkinter as tk
import sqlite3
from datetime import datetime
from datetime import timedelta

import logging

logger = logging.getLogger(__name__)

DATABASE_PATH = 'nikki.sqlite3'

class App(tk.Frame):
    def __init__(self, master):
        self._logger = logging.getLogger(f'{__name__}.App')
        super().__init__(master)

        nikkiListbox = NikkiListbox(self)
        
        ctrl_frame = tk.Frame(self)

        button_create = tk.Button(ctrl_frame, text='新規', command=nikkiListbox.create_nikki)
        button_edit = tk.Button(ctrl_frame, text='編集', command=nikkiListbox.edit_nikki)
        button_delete = tk.Button(ctrl_frame, text='削除', command=nikkiListbox.delete_nikki)

        button_create.grid(column=0, row=0)
        button_edit.grid(column=0, row=1)
        button_delete.grid(column=0, row=2)


        nikkiListbox.grid(column=0, row=0)
        ctrl_frame.grid(column=2, row=0)


class NikkiListbox(tk.Listbox):
    def __init__(self, master):
        self._logger = logging.getLogger(f'{__name__}.NikkiListbox')
        super().__init__(master)

        #初期設定
        self['selectmode'] = 'extended'
        self['height'] = 30
        self['width'] = 50
        self.bind('<Double-Button-1>', self.edit_nikki)

        self.load_nikki()

    def _conv_nikki_to_text(self, nikki):
        return '{n[id]} {n[at]} [{n[groupe]}] {n[comment]}'.format(n=nikki)

    def load_nikki(self, limit=100):
        self._logger.debug('load nikki')
        nikki_list = load_nikki_from_db(limit)
        self._nikki_list = nikki_list

        self['listvariable'] = tk.StringVar(value=[self._conv_nikki_to_text(nikki) for nikki in nikki_list])

    def delete_nikki(self):
        self._logger.debug('deleting selected nikki')
        indexes = list(self.curselection())
        if not indexes:
            self._logger.info('no contents selected')
        indexes.sort(reverse=True)
        for index in indexes:
            self._delete_nikki(index)

    def _delete_nikki(self, index):
        delete_nikki_by_id(self._nikki_list[index]['id'])
        self._nikki_list.pop(index)
        self.delete(index)

    def edit_nikki(self, *args):
        indexes = self.curselection()
        if not indexes:
            self._logger.info('no contents selected')
            return
        index = indexes[0]
        self._edit_nikki(index)

    def _edit_nikki(self, index):
        self._logger.debug('opening editor')
        editor = Editor(self, self._nikki_list[index])
        self.wait_window(editor)
        self._logger.debug('editor was closed')
        self.reload_nikki(index)

    def reload_nikki(self, index):
        nikki = load_nikki_from_db_by_id(self._nikki_list[index]['id'])
        text = self._conv_nikki_to_text(nikki)
        self._nikki_list[index] = nikki
        self.delete(index)
        self.insert(index, text)

    def create_nikki(self):
        nikki_id = create_nikki()
        nikki = load_nikki_from_db_by_id(nikki_id)
        self._nikki_list.insert(0, nikki)
        self.insert(0, self._conv_nikki_to_text(nikki))
        self._edit_nikki(0)



class Editor(tk.Toplevel):
    def __init__(self, master, nikki):
        self._logger = logging.getLogger(f'{__name__}.Editor')
        self._logger.debug('initializing editor')

        super().__init__(master)

        self.grab_set()
        
        var_id = tk.StringVar(value=nikki['id'])
        var_created = tk.StringVar(value=nikki['created'])
        var_updated = tk.StringVar(value=nikki['updated'])
        var_at = tk.StringVar(value=nikki['at'])
        var_groupe = tk.StringVar(value=nikki['groupe'])

        label_id = tk.Label(self, text='id')
        label_created = tk.Label(self, text='created')
        label_updated = tk.Label(self, text='updated')
        label_at = tk.Label(self, text='at')
        label_comment = tk.Label(self, text='comment')
        label_groupe = tk.Label(self, text='groupe')

        entry_id = tk.Entry(self, textvariable=var_id, state='readonly')
        entry_created = tk.Entry(self, textvariable=var_created, state='readonly')
        entry_updated = tk.Entry(self, textvariable=var_updated, state='readonly')
        frame_datetime = DatetimeFrame(self, var=var_at)
        text_comment = tk.Text(self)
        text_comment.insert('1.0', nikki['comment'])
        entry_groupe = tk.Entry(self, textvariable=var_groupe)

        ctrl_frame = tk.Frame(self)
        button_update = tk.Button(ctrl_frame, text='update', command=self.update)
        button_cancel = tk.Button(ctrl_frame, text='cancel', command=self.cancel)

        button_update.grid(column=0, row=0)
        button_cancel.grid(column=1, row=0)

        label_id.grid(column=0, row=0)
        label_created.grid(column=0, row=1)
        label_updated.grid(column=0, row=2)
        label_at.grid(column=0, row=3)
        label_comment.grid(column=0, row=4)
        label_groupe.grid(column=0, row=5)
        entry_id.grid(column=1, row=0)
        entry_created.grid(column=1, row=1)
        entry_updated.grid(column=1, row=2)
        frame_datetime.grid(column=1, row=3)
        text_comment.grid(column=1, row=4)
        entry_groupe.grid(column=1, row=5)
        ctrl_frame.grid(column=0, row=6, columnspan=2)

        self._var_id = var_id
        self._var_at = var_at
        self._text_comment = text_comment
        self._var_groupe = var_groupe
        
    def update(self):
        self._logger.debug('updating nikki')
        nikki_id = self._var_id.get()
        at = self._var_at.get() 
        comment = self._text_comment.get('1.0', 'end-1c')
        groupe = self._var_groupe.get()
        if groupe == '':
            groupe = None
        update_nikki(nikki_id, at, comment, groupe)
        self.destroy()

    def cancel(self):
        self.destroy()

class DatetimeFrame(tk.Frame):
    DTTM_FORMAT = '%Y-%m-%d %H:%M:%S'
    def __init__(self, master, var):
        self._logger = logging.getLogger(f'{__name__}.DatetimeFrame')
        self._logger.debug('initializing DatetimeFrame')
        super().__init__(master)

        self._var = var
        self._default_var = var.get()

        frame_top = tk.Frame(self)
        button_minus7Days = tk.Button(frame_top, text='-7日', command=self.make_add_func(timedelta(days=-7)))
        button_minus1Day = tk.Button(frame_top, text='-1日', command=self.make_add_func(timedelta(days=-1)))
        entry_at = tk.Entry(frame_top, textvariable=var)
        button_plus1Day = tk.Button(frame_top, text='+1日', command=self.make_add_func(timedelta(days=1)))
        button_plus7Days = tk.Button(frame_top, text='+7日', command=self.make_add_func(timedelta(days=7)))

        button_minus7Days.grid(column=0, row=0)
        button_minus1Day.grid(column=1, row=0)
        entry_at.grid(column=2, row=0, padx=8, pady=8)
        button_plus1Day.grid(column=3, row=0)
        button_plus7Days.grid(column=4, row=0)

        frame_bottom = tk.Frame(self)
        button_defaultTime = tk.Button(frame_bottom, text='もとに戻す', command=self.set_to_default)
        button_currentTime = tk.Button(frame_bottom, text='現在時刻', command=self.set_to_current_time)
        button_currentDatetime = tk.Button(frame_bottom, text='現在', command=self.set_to_current_datetime)
        button_truncateTime = tk.Button(frame_bottom, text='時間切り捨て', command=self.truncate_time)

        button_defaultTime.grid(column=0, row=0)
        button_currentTime.grid(column=1, row=0)
        button_currentDatetime.grid(column=2, row=0)
        button_truncateTime.grid(column=3, row=0)

        frame_top.grid(column=0, row=0)
        frame_bottom.grid(column=0, row=1)


        self._logger.debug('initializing is complete')

    def _add_to_var(self, delta):
        self._logger.debug('changing datetime')
        dttm = self.get_dttm()
        dttm += delta
        self.set_dttm(dttm)

    def get_dttm(self):
        return datetime.strptime(self._var.get(), self.DTTM_FORMAT)

    def set_dttm(self, dttm):
        self._var.set(dttm.strftime(self.DTTM_FORMAT))

    def make_add_func(self, delta):
        def func():
            self._add_to_var(delta)
        return func

    def truncate_time(self):
        self._logger.debug('truncating time')
        dttm = self.get_dttm()
        dttm = dttm.replace(hour=0, minute=0, second=0)
        self.set_dttm(dttm)

    def set_to_current_time(self):
        self._logger.debug('setting to current time')
        now = datetime.now()
        dttm = self.get_dttm()
        dttm = dttm.replace(hour=now.hour, minute=now.minute, second=now.second)
        self.set_dttm(dttm)

    def set_to_current_datetime(self):
        self._logger.debug('setting to current datetime')
        self.set_dttm(datetime.now())

    def set_to_default(self):
        self._logger.debug('setting to default')
        self._var.set(self._default_var)


#データベースに接続する
def get_db():
    """connect to db"""
    logger.debug('connecting to db')
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    return db

#データベースから指定した件数読み込む。
def load_nikki_from_db(limit=100, order='DESC'):
    """read nikki from database"""
    logger.debug('read nikki from database')
    db = None
    try:
        db = get_db()
        nikki_list = db.execute("SELECT id, DATETIME(created, 'localtime') AS created, DATETIME(updated, 'localtime') AS updated, DATETIME(at, 'localtime') AS at, comment, groupe FROM nikki ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    except sqlite3.OperationalError:
        logger.error('failed to read nikki from database')
        raise
    finally:
        if db:
            db.close()
    return nikki_list

def load_nikki_from_db_by_id(nikki_id):
    """read a nikki from database"""
    logger.debug('read a nikki from database')
    db = None
    try:
        db = get_db()
        nikki_list = db.execute("SELECT id, DATETIME(created, 'localtime') AS created, DATETIME(updated, 'localtime') AS updated, DATETIME(at, 'localtime') AS at, comment, groupe FROM nikki WHERE id = ?", (nikki_id,)).fetchall()
        if nikki_list == []:
            logger.warning('failed to load nikki : no such nikki No.{}'.format(nikki_id))
            nikki = []
        else:
            nikki = nikki_list[0]
    except sqlite3.OperationalError:
        logger.error('failed to read nikki from database')
        raise
    finally:
        if db:
            db.close()
    return nikki

def create_nikki():
    logger.debug('creating a new nikki')
    db = None
    try:
        db = get_db()
        db.execute("INSERT INTO nikki(comment, groupe) VALUES('', NULL)")
        nikki_id = db.execute('SELECT id FROM nikki ORDER BY id DESC LIMIT 1').fetchone()[0]
        db.commit()
    except sqlite3.OperationalError:
        logger.error('failed to create nikki')
        raise
    finally:
        if db:
            db.close()
    return nikki_id

def delete_nikki_by_id(nikki_id):
    """delete nikki"""
    logger.debug('deleting nikki No.{}'.format(nikki_id))
    db = None
    try:
        db = get_db()
        db.execute('INSERT INTO backup(created, updated, at, comment, groupe) SELECT created, updated, at, comment, groupe FROM nikki WHERE id = ?', (nikki_id,))
        db.execute('DELETE FROM nikki WHERE id = ?', (nikki_id,))
        db.commit()
    except sqlite3.OperationalError:
        logger.error('failed to delete nikki')
        raise
    finally:
        if db:
            db.close()

def update_nikki(nikki_id, at, comment, groupe):
    """update nikki"""
    logger.debug('updating nikki No.{}'.format(nikki_id))
    db = None
    try:
        db = get_db()
        db.execute("UPDATE nikki SET updated = CURRENT_TIMESTAMP, at = DATETIME(?, 'utc'), comment = ?, groupe = ? WHERE id = ?", (at, comment, groupe, nikki_id))
        db.commit()
        logger.debug('updating nikki is complete')
    except sqlite3.OperationalError:
        logger.error('failed to update nikki')
        raise
    finally:
        if db:
            db.close()




if __name__ == '__main__':
    LOGLEVEL = logging.DEBUG
    logger.setLevel(LOGLEVEL)
    streamHandler = logging.StreamHandler()
    streamHandler.setLevel(LOGLEVEL)
    streamHandler.setFormatter(logging.Formatter('%(levelname)s - %(name)s - %(message)s'))
    logger.addHandler(streamHandler)

    window = tk.Tk()
    app = App(window)
    app.pack()
    app.mainloop()
