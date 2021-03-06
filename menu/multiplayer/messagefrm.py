try: from sleekxmpp.jid import JID
except ImportError:  # sleekxmpp requires openssl 1.0.2
    print 'OpenSSL 1.0.2 not detected'
from panda3d.core import TextNode
from direct.gui.DirectGuiGlobals import FLAT, NORMAL, DISABLED, ENTER, EXIT
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectScrolledFrame import DirectScrolledFrame
from direct.gui.DirectLabel import DirectLabel
from yyagl.library.gui import Btn, Entry
from direct.gui.OnscreenText import OnscreenText
from yyagl.gameobject import GameObject
from yyagl.engine.gui.imgbtn import ImgBtn


class Chat(GameObject):

    def __init__(self, dst):
        GameObject.__init__(self)
        self.dst = dst
        self.messages = []
        self.read = True
        self.closed = False

    @property
    def title(self):
        return JID(self.dst).bare


class MUC(Chat):

    def __init__(self, dst):
        Chat.__init__(self, dst)
        self.users = []

    @property
    def title(self):
        is_me = lambda usr: usr == self.eng.xmpp.client.boundjid.bare
        return ', '.join(sorted(self.users, key=is_me))


class MatchMsgFrm(GameObject):

    def __init__(self, menu_args):
        GameObject.__init__(self)
        self.eng.log('created match message form')
        self.chat = None
        self.msg_frm = DirectFrame(
            frameSize=(-.02, 2.5, 0, 1.22),
            frameColor=(.2, .2, .2, .5),
            pos=(.04, 1, -1.69), parent=base.a2dTopLeft)
        t_a = menu_args.text_args
        t_a['scale'] = .05
        t_a['fg'] = menu_args.text_normal
        self.dst_txt = OnscreenText(
            text='', pos=(0, 1.16), parent=self.msg_frm, align=TextNode.A_left,
            **t_a)
        self.ent = Entry(
            scale=.04, pos=(0, 1, .03), entryFont=menu_args.font, width=62,
            frameColor=menu_args.btn_color, parent=self.msg_frm,
            initialText=_('write here your message'),
            command=self.on_typed_msg, focusInCommand=self.on_focus,
            focusInExtraArgs=['in'], focusOutCommand=self.on_focus,
            focusOutExtraArgs=['out'], text_fg=menu_args.text_active)
        self.ent['state'] = DISABLED
        self.txt_frm = DirectScrolledFrame(
            frameSize=(-.02, 2.46, -.02, 1.02),
            canvasSize=(-.02, 2.42, -.02, 1.02),
            scrollBarWidth=.036,
            verticalScroll_relief=FLAT,
            verticalScroll_frameColor=(.2, .2, .2, .4),
            verticalScroll_thumb_relief=FLAT,
            verticalScroll_thumb_frameColor=(.8, .8, .8, .6),
            verticalScroll_incButton_relief=FLAT,
            verticalScroll_incButton_frameColor=(.8, .8, .8, .6),
            verticalScroll_decButton_relief=FLAT,
            verticalScroll_decButton_frameColor=(.8, .8, .8, .6),
            horizontalScroll_relief=FLAT,
            frameColor=(1, 1, 1, .0),
            pos=(.02, 1, .11), parent=self.msg_frm)
        t_a['scale'] = .046
        self.msg_txt = OnscreenText(
            text='', pos=(0, .24), parent=self.txt_frm.getCanvas(),
            align=TextNode.A_left, wordwrap=52, **t_a)
        lab_args = menu_args.label_args
        lab_args['scale'] = .046
        lab_args['text_fg'] = menu_args.text_normal
        self.lab_frm = Btn(
            frameSize=(-.02, 2.5, -.01, .05),
            frameColor=(1, 1, 1, 0),
            pos=(0, 1, 1.15), parent=self.msg_frm)
        self.lab_frm.bind(ENTER, self.on_enter)
        self.lab_frm.bind(EXIT, self.on_exit)
        self.tooltip = DirectLabel(
            text='', pos=(2.4, 1, -.06),
            parent=self.lab_frm, text_wordwrap=50, text_bg=(.2, .2, .2, .8),
            text_align=TextNode.A_right, **lab_args)
        self.tooltip.set_bin('gui-popup', 10)
        self.tooltip.hide()

    def on_enter(self, pos):
        self.tooltip.show()

    def on_exit(self, pos):
        self.tooltip.hide()

    def add_msg_txt(self, msg):
        self.msg_txt['text'] += ('\n' if self.msg_txt['text'] else '') + msg
        txt_height = self.msg_txt.textNode.getUpperLeft3d()[2] - \
            self.msg_txt.textNode.getLowerRight3d()[2]
        self.txt_frm['canvasSize'] = (-.02, .72, .28 - txt_height, .28)

    def set_title(self, title):
        ttitle = self.trunc(title, 160)
        fix_name = lambda name: name if '@' not in name else name.split('@')[0] + '\1smaller\1@' + name.split('@')[1] + '\2'
        if title:
            if ',' in ttitle:
                is_muc = True
                ttitle = ttitle
                names = ttitle.split(',')
                names = [name.strip() for name in names]
                names = [fix_name(name) for name in names]
                ttitle = ', '.join(names)
            else:
                ttitle = fix_name(ttitle)
        self.dst_txt['text'] = ttitle
        self.tooltip['text'] = title

    @staticmethod
    def trunc(name, lgt):
        if len(name) > lgt: return name[:lgt] + '...'
        return name

    def on_typed_msg(self, val):
        #self.add_msg_txt('\1italic\1' + _('you') + '\2: ' + val)
        self.ent.set('')
        self.eng.xmpp.client.send_message(
            mfrom=self.eng.xmpp.client.boundjid.full,
            mto=self.chat.dst,
            mtype='groupchat',
            mbody=val)
        self.ent['focus'] = 1

    def on_groupchat_msg(self, msg):
        src = str(JID(msg['mucnick']))
        src = src.split('@')[0] + '\1smaller\1@' + src.split('@')[1] + '\2'
        self.eng.log('received groupchat message from %s in the chat %s' %(msg['mucnick'], JID(msg['from']).bare))
        str_msg = '\1italic\1' + src + '\2: ' + str(msg['body'])
        if not self.chat:
            self.chat = MUC(str(JID(msg['from']).bare))
        self.chat.messages += [str_msg]
        if self.dst_txt['text'] == '':
            self.set_chat(self.chat)
        elif self.chat.dst == str(JID(msg['from']).bare):
            self.add_msg_txt(str_msg)

    def on_presence_available_room(self, msg):
        room = str(JID(msg['muc']['room']).bare)
        nick = str(msg['muc']['nick'])
        self.eng.log('user %s has logged in the chat %s' %(nick, room))
        self.chat.users += [nick]
        self.set_title(self.chat.title)

    def on_presence_unavailable_room(self, msg):
        room = str(JID(msg['muc']['room']).bare)
        nick = str(msg['muc']['nick'])
        self.eng.log('user %s has left the chat %s' %(nick, room))
        self.chat.users.remove(nick)
        self.set_title(self.chat.title)

    def add_groupchat(self, room, usr):
        self.set_title(usr)
        if not self.chat:
            self.chat = MUC(room)
        self.set_chat(self.chat)

    def set_chat(self, chat):
        self.set_title(chat.title)
        self.msg_txt['text'] = '\n'.join(chat.messages)
        txt_height = self.msg_txt.textNode.getUpperLeft3d()[2] - \
            self.msg_txt.textNode.getLowerRight3d()[2]
        self.txt_frm['canvasSize'] = (-.02, .72, .28 - txt_height, .28)
        self.ent['state'] = NORMAL

    def on_focus(self, val):
        if val == 'in' and self.ent.get() == _('write here your message'):
            self.ent.set('')
        self.notify('on_match_msg_focus', val)

    def destroy(self):
        self.eng.log('message form destroyed')
        self.msg_frm.destroy()
        GameObject.destroy(self)

class MessageFrm(GameObject):

    def __init__(self, menu_args):
        GameObject.__init__(self)
        self.eng.log('created message form')
        self.chats = []
        self.curr_chat = None
        self.curr_match_room = None
        self.msg_frm = DirectFrame(
            frameSize=(-.02, .8, 0, .45),
            frameColor=(.2, .2, .2, .5),
            pos=(-.82, 1, .02), parent=base.a2dBottomRight)
        self.presences_sent = []
        self.menu_args = menu_args
        t_a = menu_args.text_args
        t_a['scale'] = .05
        t_a['fg'] = menu_args.text_normal
        self.dst_txt = OnscreenText(
            text='', pos=(0, .4), parent=self.msg_frm, align=TextNode.A_left,
            **t_a)
        self.arrow_btn = ImgBtn(
            parent=self.msg_frm, scale=.024, pos=(.7, 1, .42),
            frameColor=(1, 1, 1, 1),
            frameTexture='assets/images/gui/arrow.txo',
            command=self.on_arrow,
            **menu_args.imgbtn_args)
        self.arrow_btn.disable()
        self.close_btn = ImgBtn(
            parent=self.msg_frm, scale=.024, pos=(.76, 1, .42),
            frameColor=(1, 1, 1, 1),
            frameTexture='assets/images/gui/close.txo',
            command=self.on_close,
            **menu_args.imgbtn_args)
        self.close_btn.disable()
        self.ent = Entry(
            scale=.04, pos=(0, 1, .03), entryFont=menu_args.font, width=19.5,
            frameColor=menu_args.btn_color, parent=self.msg_frm,
            initialText=_('write here your message'),
            command=self.on_typed_msg, focusInCommand=self.on_focus,
            focusInExtraArgs=['in'], focusOutCommand=self.on_focus,
            focusOutExtraArgs=['out'], text_fg=menu_args.text_active)
        self.ent['state'] = DISABLED
        self.txt_frm = DirectScrolledFrame(
            frameSize=(-.02, .76, -.02, .28),
            canvasSize=(-.02, .72, -.02, .28),
            scrollBarWidth=.036,
            verticalScroll_relief=FLAT,
            verticalScroll_frameColor=(.2, .2, .2, .4),
            verticalScroll_thumb_relief=FLAT,
            verticalScroll_thumb_frameColor=(.8, .8, .8, .6),
            verticalScroll_incButton_relief=FLAT,
            verticalScroll_incButton_frameColor=(.8, .8, .8, .6),
            verticalScroll_decButton_relief=FLAT,
            verticalScroll_decButton_frameColor=(.8, .8, .8, .6),
            horizontalScroll_relief=FLAT,
            frameColor=(1, 1, 1, 0),
            pos=(.02, 1, .11), parent=self.msg_frm)
        t_a['scale'] = .046
        self.msg_txt = OnscreenText(
            text='', pos=(0, .24), parent=self.txt_frm.getCanvas(),
            align=TextNode.A_left, wordwrap=14, **t_a)
        lab_args = menu_args.label_args
        lab_args['scale'] = .046
        lab_args['text_fg'] = menu_args.text_normal
        self.lab_frm = Btn(
            frameSize=(-.02, .64, -.01, .05),
            frameColor=(1, 1, 1, 0),
            pos=(0, 1, .4), parent=self.msg_frm)
        self.lab_frm.bind(ENTER, self.on_enter)
        self.lab_frm.bind(EXIT, self.on_exit)
        self.tooltip = DirectLabel(
            text='', pos=(.78, 1, -.06),
            parent=self.lab_frm, text_wordwrap=16, text_bg=(.2, .2, .2, .8),
            text_align=TextNode.A_right, **lab_args)
        self.tooltip.set_bin('gui-popup', 10)
        self.tooltip.hide()

    def on_enter(self, pos):
        self.tooltip.show()

    def on_exit(self, pos):
        self.tooltip.hide()

    def show(self):
        self.msg_frm.show()

    def hide(self):
        self.msg_frm.hide()

    def add_msg_txt(self, msg):
        self.msg_txt['text'] += ('\n' if self.msg_txt['text'] else '') + msg
        txt_height = self.msg_txt.textNode.getUpperLeft3d()[2] - \
            self.msg_txt.textNode.getLowerRight3d()[2]
        self.txt_frm['canvasSize'] = (-.02, .72, .28 - txt_height, .28)

    def set_title(self, title):
        ttitle = self.trunc(title, 32)
        fix_name = lambda name: name if '@' not in name else name.split('@')[0] + '\1smaller\1@' + name.split('@')[1] + '\2'
        if title:
            if ',' in ttitle:
                is_muc = True
                ttitle = ttitle
                names = ttitle.split(',')
                names = [name.strip() for name in names]
                names = [fix_name(name) for name in names]
                ttitle = ', '.join(names)
            else:
                ttitle = fix_name(ttitle)
        self.dst_txt['text'] = ttitle
        self.tooltip['text'] = title

    @staticmethod
    def trunc(name, lgt):
        if len(name) > lgt: return name[:lgt] + '...'
        return name

    def set_chat(self, chat):
        self.curr_chat = chat
        self.set_title(chat.title)
        self.msg_txt['text'] = '\n'.join(chat.messages)
        txt_height = self.msg_txt.textNode.getUpperLeft3d()[2] - \
            self.msg_txt.textNode.getLowerRight3d()[2]
        self.txt_frm['canvasSize'] = (-.02, .72, .28 - txt_height, .28)
        if not self.chats:
            self.close_btn.disable()
            self.ent['state'] = DISABLED
        elif len(self.chats) == 1:
            self.close_btn.enable()
            self.ent['state'] = NORMAL
            self.arrow_btn.disable()
        else:
            self.close_btn.enable()
            self.ent['state'] = NORMAL
            self.arrow_btn.enable()
        if all(_chat.read for _chat in self.chats):
            self.arrow_btn['frameTexture'] = 'assets/images/gui/arrow.txo'
        else:
            self.arrow_btn['frameTexture'] = 'assets/images/gui/message.txo'

    def on_arrow(self):
        chat_idx = self.chats.index(self.curr_chat)
        next_idx = (chat_idx + 1) % len(self.chats)
        chat = self.chats[next_idx]
        self.set_title(chat.title)
        chat.read = True
        self.set_chat(chat)

    @property
    def open_chats(self):
        return [chat for chat in self.chats if not chat.closed]

    def on_close(self):
        if self.curr_chat not in self.open_chats: return
        curr_idx = self.open_chats.index(self.curr_chat)
        #self.chats.remove(self.curr_chat)
        self.curr_chat.closed = True
        if self.open_chats:
            self.set_chat(self.open_chats[curr_idx - 1])
        else:
            self.set_chat(Chat(''))
            self.notify('on_close_all_chats')

    def on_typed_msg(self, val):
        self.add_msg_txt('\1italic\1' + _('you') + '\2: ' + val)
        self.ent.set('')
        if self.curr_chat.dst not in self.presences_sent and \
                not str(self.curr_chat.dst).startswith('yorg'):
            self.eng.xmpp.client.send_presence(
                pfrom=self.eng.xmpp.client.boundjid.full,
                pto=self.curr_chat.dst)
            self.presences_sent += [self.curr_chat.dst]
        if str(self.curr_chat.dst).startswith('yorg'):
            self.eng.xmpp.client.send_message(
                mfrom=self.eng.xmpp.client.boundjid.full,
                mto=self.curr_chat.dst,
                mtype='groupchat',
                mbody=val)
        else:
            self.eng.xmpp.client.send_message(
                mfrom=self.eng.xmpp.client.boundjid.full,
                mto=self.curr_chat.dst,
                msubject='chat',
                mbody=val)
        msg = '\1italic\1' + _('you') + '\2: ' + val
        self.curr_chat.messages += [msg]
        self.ent['focus'] = 1

    def on_msg(self, msg):
        src = str(JID(msg['from']).bare)
        src = src.split('@')[0] + '\1smaller\1@' + src.split('@')[1] + '\2'
        str_msg = '\1italic\1' + src + '\2: ' + str(msg['body'])
        chat = self.__find_chat(msg['from'])
        if not chat:
            chat = Chat(msg['from'])
            self.chats += [chat]
        chat.messages += [str_msg]
        if self.dst_txt['text'] == '':
            self.set_chat(chat)
        elif JID(self.curr_chat.dst).bare == JID(msg['from']).bare:
            self.add_msg_txt(str_msg)
        else:
            chat.read = False
            chat.closed = False
            self.arrow_btn['frameTexture'] = 'assets/images/gui/message.txo'

    def on_groupchat_msg(self, msg):
        if str(JID(msg['from']).bare) == self.curr_match_room:
            if self.match_msg_frm:  # we're still in the room page
                self.match_msg_frm.on_groupchat_msg(msg)
        src = str(JID(msg['mucnick']))
        src = src.split('@')[0] + '\1smaller\1@' + src.split('@')[1] + '\2'
        self.eng.log('received groupchat message from %s in the chat %s' %(msg['mucnick'], JID(msg['from']).bare))
        str_msg = '\1italic\1' + src + '\2: ' + str(msg['body'])
        chat = self.curr_chat
        if not chat:
            chat = MUC(str(JID(msg['from']).bare))
            self.chats += [chat]
        chat.messages += [str_msg]
        if self.dst_txt['text'] == '':
            self.set_chat(chat)
        elif self.curr_chat.dst == str(JID(msg['from']).bare):
            self.add_msg_txt(str_msg)
        else:
            chat.read = False
            chat.closed = False
            self.arrow_btn['frameTexture'] = 'assets/images/gui/message.txo'

    def on_presence_available_room(self, msg):
        if str(JID(msg['from']).bare) == self.curr_match_room:
            self.match_msg_frm.on_presence_available_room(msg)
            return
        room = str(JID(msg['muc']['room']).bare)
        nick = str(msg['muc']['nick'])
        self.eng.log('user %s has logged in the chat %s' %(nick, room))
        chat = self.__find_chat(room)
        chat.users += [nick]
        if self.curr_chat.dst == room:
            self.set_title(chat.title)

    def on_presence_unavailable_room(self, msg):
        if self.match_msg_frm and str(JID(msg['from']).bare) == self.curr_match_room:
            self.match_msg_frm.on_presence_unavailable_room(msg)
            return
        room = str(JID(msg['muc']['room']).bare)
        nick = str(msg['muc']['nick'])
        self.eng.log('user %s has left the chat %s' %(nick, room))
        chat = self.__find_chat(room)
        if nick == self.eng.xmpp.client.boundjid.bare:
            self.on_close()
        else:
            chat.users.remove(nick)
            if self.curr_chat.dst == room:
                self.set_title(chat.title)

    def __find_chat(self, dst):
        chats = [chat for chat in self.chats if chat.dst == dst]
        if chats: return chats[0]

    def add_chat(self, usr):
        self.set_title(JID(usr).bare)
        chat = self.__find_chat(usr)
        if not chat:
            chat = Chat(usr)
            self.chats += [chat]
        self.set_chat(chat)
        self.ent['focus'] = 1

    def add_groupchat(self, room, usr):
        self.set_title(usr)
        chat = self.__find_chat(room)
        if not chat:
            chat = MUC(room)
            self.chats += [chat]
        chat.users += [usr]
        self.set_chat(chat)
        self.add_match_chat(room, usr)

    def remove_groupchat(self):
        self.match_msg_frm.detach(self.on_match_msg_focus)
        self.match_msg_frm = self.match_msg_frm.destroy()

    def on_focus(self, val):
        if val and self.ent.get() == _('write here your message'):
            self.ent.set('')
        self.notify('on_msg_focus', val)

    def on_match_msg_focus(self, val):
        self.notify('on_msg_focus', val)

    def on_room_back(self):
        self.curr_match_room = None
        self.match_msg_frm.destroy()

    def add_match_chat(self, room, usr):
        if self.curr_match_room: return
        self.curr_match_room = room
        self.match_msg_frm = MatchMsgFrm(self.menu_args)
        self.match_msg_frm.attach(self.on_match_msg_focus)
        self.match_msg_frm.add_groupchat(room, usr)
