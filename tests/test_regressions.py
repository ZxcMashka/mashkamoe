# Run with Python 2.7; client APIs are fakes, no game is launched.
import imp, os, sys, tempfile, types, unittest, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
class Event(list):
    def __iadd__(self, fn): self.append(fn); return self
    def __isub__(self, fn): self.remove(fn); return self
    def __call__(self, *args):
        for fn in list(self): fn(*args)

bw = types.ModuleType('BigWorld'); sys.modules['BigWorld'] = bw
bw.jobs = {}; bw.serial = 0
def callback(delay, fn):
    bw.serial += 1; bw.jobs[bw.serial] = fn; return bw.serial
bw.callback = callback
bw.cancelCallback = lambda token: bw.jobs.pop(token, None)
bw.time = lambda: 100.0
realm = types.ModuleType('realm'); realm.CURRENT_REALM='ASIA';sys.modules['realm']=realm
m=imp.load_source('mod_test', os.path.join(ROOT,'src','mod_mashkamarks.py'))
class Regression(unittest.TestCase):
    def setUp(self):
        m.fini(); m._state.clear(); m._subscriptions[:]=[]; m._hooks[:]=[];m._callbacks.clear();bw.jobs.clear()
        realm.CURRENT_REALM='ASIA'
        self.tmp=tempfile.mkdtemp();m.CONFIG_DIR=self.tmp+'/'
        m.TABLE_FILE=self.tmp+'/table.json';m.TABLE_PART=self.tmp+'/part';m.PENDING_FILE=self.tmp+'/pending.json'
        self.fetch=m._fetchTable;m._fetchTable=lambda:None
    def tearDown(self): m._fetchTable=self.fetch
    def test_region_aliases(self):
        for value,want in [('ASIA','asia'),('SEA','asia'),('EU','eu'),('NA','na'),('RU',None)]:
            realm.CURRENT_REALM=value; self.assertEqual(m._region(),want)
    def test_realms_never_fall_back_to_eu(self):
        raw=json.dumps({'realms':{'eu':{'thresholds':{'17':{'65':1000}}}}})
        self.assertIsNone(m._parseTable(raw))
    def test_asia_table(self):
        raw=json.dumps({'realms':{'eu':{'thresholds':{'17':{'65':1000}}},'asia':{'thresholds':{'17':{'65':2000}}}}})
        self.assertEqual(m._parseTable(raw)[17][65],2000)
    def test_unlabelled_only_trusted_regional_endpoint(self):
        raw=json.dumps([{'tank_id':17,'moe1':2222}])
        self.assertIsNone(m._parseTable(raw))
        self.assertEqual(m._parseTable(raw,'asia')[17][65],2222)
        self.assertIsNone(m._parseTable(raw,'eu'))
    def test_explicit_wrong_region_rejected_even_trusted(self):
        self.assertIsNone(m._parseTable(json.dumps({'region':'eu','rows':{'17':{'65':10}}}),'asia'))
    def test_wrong_cache_and_bundled_seed_rejected(self):
        open(m.TABLE_FILE,'wb').write(json.dumps({'region':'eu','at':9999999999,'rows':{'17':{'65':1111}}}))
        self.assertFalse(m._tableSeed());self.assertFalse(m._table())
    def test_matching_cache_loaded(self):
        open(m.TABLE_FILE,'wb').write(json.dumps({'region':'asia','at':9999999999,'rows':{'17':{'65':2222}},'mastery':{'17':{'ace':1000}}}))
        self.assertEqual(m._table()[17][65],2222);self.assertEqual(m._state['masteryTable'][17]['ace'],1000)
    def test_region_switch_clears_memory(self):
        m._state.update(tableRegion='eu',table={17:{65:1234}},masteryTable={17:{'ace':999}},tableBusy=True,snapshot={'table':1})
        self.assertFalse(m._table());self.assertNotIn('masteryTable',m._state);self.assertNotIn('snapshot',m._state)
    def test_untagged_neighbour_rejected(self):
        path=self.tmp+'/neighbour';open(path,'wb').write(json.dumps({'marks':{'fetchedAt':9999999999,'tanks':{'17':[0,1,2,3,4]}}}))
        old=m.NEIGHBOURS;m.NEIGHBOURS=[path]
        try:self.assertFalse(m._tableFromNeighbour())
        finally:m.NEIGHBOURS=old
    def test_summary_single_event_authoritative(self):
        class Summary(object):
            def getTotalDamage(self):return 500
            def getTotalStunDamage(self):return 5
            def getTotalBlockedDamage(self):return 10
        event=Summary();setattr(event,m._SUM_RADIO,200);setattr(event,m._SUM_TRACK,300)
        m._state.update(battleActive=True,bt={'dmg':999})
        m._onSummary(event);cell=m._state['bt'];self.assertEqual((cell['dmg'],cell['radio'],cell['track']),(500,200,300))
        m._onSummary(event);self.assertEqual(cell['dmg'],500)
    def test_native_hidden_filter(self):
        class Extra(object):
            def __init__(self,hidden):self.hidden=hidden
            def isNone(self):return self.hidden
            def getDamage(self):return 50
        class Feedback(object):
            def __init__(self,hidden):self.hidden=hidden
            def getType(self):return 1
            def getExtra(self):return Extra(self.hidden)
        m._state.update(battleActive=True,bt={'dmg':0},feMap={1:'dmg'})
        m._onFeedback([Feedback(True),Feedback(False)]);self.assertEqual(m._state['bt']['dmg'],50)
    def test_feedback_after_leaving_ignored(self):
        m._state['battleActive']=False;m._onFeedback([object()]);self.assertNotIn('bt',m._state)
    def test_subscription_idempotency_and_cleanup(self):
        event=Event();fn=lambda:None
        for _ in range(3):m._listen(event,fn,'battle')
        self.assertEqual(len(event),1);m._clearScope('battle');self.assertEqual(len(event),0)
    def test_timer_cancel_and_late_callback_after_unload(self):
        called=[];token=m._schedule(1,lambda:called.append(1),'battle');late=bw.jobs[token]
        m._clearScope('battle');self.assertNotIn(token,bw.jobs);late();self.assertEqual(called,[])
        token=m._schedule(1,lambda:called.append(2));late=bw.jobs[token];m.fini();late();self.assertEqual(called,[])
    def test_repeated_garage_battle_scopes(self):
        ev=Event();hits=[]
        for _ in range(30):
            m._listen(ev,lambda:hits.append(1),'lobby');m._schedule(1,lambda:None,'lobby');m._clearScope('lobby')
            m._listen(ev,lambda:hits.append(1),'battle');m._schedule(1,lambda:None,'battle');m._clearScope('battle')
            self.assertEqual(len(ev),0);self.assertEqual(len(bw.jobs),0)
    def test_early_leave_pending_park_only_once(self):
        snap={'cd':17,'name':'Tank'};cell={'id':123,'name':'Tank','snap':snap,'dmg':100}
        m._state.update(bt=cell,snapshot=snap,battleActive=True)
        m._onBattleEnd();m._onBattleEnd();self.assertEqual(len(m._pendingQueue()),1)
        self.assertEqual(m._pendingQueue()[0]['bt']['dmg'],100)
    def test_foreign_hook_chain_preserved_and_deactivated(self):
        class Avatar(object):pass
        old=lambda *a:1;wrapper=lambda *a:2;foreign=lambda *a:3
        Avatar.handleKey=foreign;active=[True]
        m._hooks.append((Avatar,'handleKey',old,wrapper,'battle',active));m._clearScope('battle')
        self.assertIs(Avatar.handleKey.im_func,foreign);self.assertFalse(active[0])
    def test_engine_response_after_region_switch_ignored(self):
        saved=[];bw.fetchURL=lambda url,fn,*args:saved.append(fn)
        m._fetchViaEngine('https://example.test',lambda *a:self.fail('stale response accepted'))
        realm.CURRENT_REALM='EU'
        saved[0](object())
    def test_unload_and_reinit_no_duplicate_global_subscriptions(self):
        pe=types.ModuleType('PlayerEvents');pe.g_playerEvents=types.SimpleNamespace() if hasattr(types,'SimpleNamespace') else type('PE',(),{})()
        for n in ('onAccountShowGUI','onAvatarBecomePlayer','onAvatarReady','onAvatarBecomeNonPlayer'):setattr(pe.g_playerEvents,n,Event())
        sys.modules['PlayerEvents']=pe
        olda,oldb=m._lobbyPackage,m._startHook;m._lobbyPackage=lambda:None;m._startHook=lambda _:None
        try:
            for _ in range(5):
                m.init();m.init();self.assertEqual(len(pe.g_playerEvents.onAvatarReady),1)
                m.fini();self.assertEqual(len(pe.g_playerEvents.onAvatarReady),0)
        finally:m._lobbyPackage,m._startHook=olda,oldb

    def test_battle_subscribes_to_single_summary_signal_and_unsubscribes(self):
        
        for name in ('skeletons','skeletons.gui'):
            sys.modules[name]=types.ModuleType(name);sys.modules[name].__path__=[]
        helpers=types.ModuleType('helpers');sk=types.ModuleType('skeletons.gui.battle_session');sk.IBattleSessionProvider=object
        session=type('Session',(),{})();session.shared=type('Shared',(),{})();feedback=type('Feedback',(),{})()
        feedback.onPlayerFeedbackReceived=Event();feedback.onPlayerSummaryFeedbackReceived=Event();session.shared.feedback=feedback
        helpers.dependency=type('Dependency',(),{'instance':staticmethod(lambda _:session)})();sys.modules['helpers']=helpers;sys.modules['skeletons.gui.battle_session']=sk
        saved={}
        for name in ('_battleIsRandom','_battleKeys','_killCamWatch','_battleOpen'):
            saved[name]=getattr(m,name);setattr(m,name,lambda:True)
        try:
            m._onBattleStart();m._onBattleStart()
            self.assertEqual(list(feedback.onPlayerSummaryFeedbackReceived),[m._onSummary])
            self.assertEqual(list(feedback.onPlayerFeedbackReceived),[m._onFeedback])
            m._onBattleEnd();self.assertFalse(feedback.onPlayerFeedbackReceived);self.assertFalse(feedback.onPlayerSummaryFeedbackReceived)
        finally:
            for name,value in saved.items():setattr(m,name,value)
    def test_real_key_hook_restored(self):
        keys=types.ModuleType('Keys')
        keys.KEY_LALT=1;keys.KEY_RALT=2;keys.KEY_LCONTROL=3;keys.KEY_RCONTROL=4;sys.modules['Keys']=keys
        avatar=types.ModuleType('Avatar')
        class PlayerAvatar(object):
            def handleKey(self,*a,**kw):return 'original'
        avatar.PlayerAvatar=PlayerAvatar;sys.modules['Avatar']=avatar
        original=PlayerAvatar.handleKey.im_func
        m._battleKeys();self.assertIsNot(PlayerAvatar.handleKey.im_func,original)
        self.assertEqual(PlayerAvatar().handleKey(True,1,0),'original')
        m._clearScope('battle');self.assertIs(PlayerAvatar.handleKey.im_func,original)
    def test_eu_seed_is_accepted_only_for_eu(self):
        realm.CURRENT_REALM='EU'
        self.assertTrue(m._tableSeed())
        self.assertEqual(json.load(open(m.TABLE_FILE))['region'],'eu')
        realm.CURRENT_REALM='NA';self.assertFalse(m._tableSeed());self.assertFalse(m._table())
    def test_matching_neighbour_with_provenance(self):
        path=self.tmp+'/neighbour';open(path,'wb').write(json.dumps({'region':'asia','marks':{'fetchedAt':9999999999,'tanks':{'17':[0,1,2,3,4]}}}))
        old=m.NEIGHBOURS;m.NEIGHBOURS=[path]
        try:
            self.assertTrue(m._tableFromNeighbour());self.assertEqual(m._state['table'][17][65],1)
            self.assertEqual(json.load(open(m.TABLE_FILE))['region'],'asia')
        finally:m.NEIGHBOURS=old

if __name__=='__main__':unittest.main(verbosity=2)
