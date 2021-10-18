import tkinter as tk
import sqlite3

import logging

logger = logging.getLogger(__name__)

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

        self.load_nikki()

    def _conv_nikki_to_text(self, nikki):
        return '{} {} [{}] {}'.format(nikki[0], nikki[1], nikki[3], nikki[2][:20])

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
        delete_nikki_by_id(self._nikki_list[index][0])
        self._nikki_list.pop(index)
        self.delete(index)

    def edit_nikki(self):
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
        nikki = load_nikki_from_db_by_id(self._nikki_list[index][0])
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
        self._logger.info('initializing editor')

        super().__init__(master)

        self.grab_set()
        
        var_id = tk.StringVar(value=nikki[0])
        var_created = tk.StringVar(value=nikki[1])
        var_groupe = tk.StringVar(value=nikki[3])

        label_id = tk.Label(self, text='id')
        label_created = tk.Label(self, text='created')
        label_comment = tk.Label(self, text='comment')
        label_groupe = tk.Label(self, text='groupe')

        entry_id = tk.Entry(self, textvariable=var_id, state='readonly')
        entry_created = tk.Entry(self, textvariable=var_created)
        text_comment = tk.Text(self)
        text_comment.insert('1.0', nikki[2])
        entry_groupe = tk.Entry(self, textvariable=var_groupe)

        ctrl_frame = tk.Frame(self)
        button_update = tk.Button(ctrl_frame, text='update', command=self.update)
        button_cancel = tk.Button(ctrl_frame, text='cancel', command=self.cancel)

        button_update.grid(column=0, row=0)
        button_cancel.grid(column=1, row=0)

        label_id.grid(column=0, row=0)
        label_created.grid(column=0, row=1)
        label_comment.grid(column=0, row=2)
        label_groupe.grid(column=0, row=3)
        entry_id.grid(column=1, row=0)
        entry_created.grid(column=1, row=1)
        text_comment.grid(column=1, row=2)
        entry_groupe.grid(column=1, row=3)
        ctrl_frame.grid(column=0, row=4, columnspan=2)

        self._var_id = var_id
        self._var_created = var_created
        self._text_comment = text_comment
        self._var_groupe = var_groupe
        
    def update(self):
        self._logger.debug('updating nikki')
        nikki_id = self._var_id.get()
        created = self._var_created.get() 
        comment = self._text_comment.get('1.0', 'end-1c')
        groupe = self._var_groupe.get()
        if groupe == '':
            groupe = None
        update_nikki(nikki_id, created, comment, groupe)
        self.destroy()

    def cancel(self):
        self.destroy()




def get_db():
    return sqlite3.connect('nikki.sqlite3')

def load_nikki_from_db(limit=100, order='DESC'):
    """read nikki from database"""
    logger.debug('read nikki from database')
    db = None
    try:
        db = get_db()
        nikki_list = db.execute("SELECT id, DATETIME(created, 'localtime'), comment, groupe FROM nikki ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
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
        nikki_list = db.execute("SELECT id, DATETIME(created, 'localtime'), comment, groupe FROM nikki WHERE id = ?", (nikki_id,)).fetchall()
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
        db.execute('DELETE FROM nikki WHERE id = ?', (nikki_id,))
        db.commit()
    except sqlite3.OperationalError:
        logger.error('failed to delete nikki')
        raise
    finally:
        if db:
            db.close()

def update_nikki(nikki_id, created, comment, groupe):
    """update nikki"""
    logger.debug('updating nikki No.{}'.format(nikki_id))
    db = None
    try:
        db = get_db()
        db.execute("UPDATE nikki SET created = DATETIME(?, 'utc'), comment = ?, groupe = ? WHERE id = ?", (created, comment, groupe, nikki_id))
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
    streamHandler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(streamHandler)

    window = tk.Tk()
    app = App(window)
    app.pack()
    app.mainloop()
