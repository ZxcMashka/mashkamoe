"""Exercise complete shipped scripts in Chromium with a fake Gameface model.
Run: python3 tests/test_browser.py [--baseline]
The baseline option loads the previous Git version to reproduce the reported bug.
"""
import json, subprocess, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'package/res/gui/gameface/mods/mashka_marks'
baseline='--baseline' in sys.argv

def asset(name):
    if baseline:
        return subprocess.check_output(['git','show','79f17c6:'+str((ASSETS/name).relative_to(ROOT))],cwd=ROOT).decode()
    text=(ASSETS/name).read_text()
    if name=='panel.js':
        text=text.replace('window.MM_CLEANUP_panel=mmCleanup;', 'window.MM_CLEANUP_panel=mmCleanup;window.mmTestStats=function(){mmPrune();return {listeners:mmListeners.length,timers:mmTimers.length,frames:mmFrames.length}};')
    return text

fixture={'ok':True,'lang':'en','cd':55937,'name':'Ambassador','tier':8,'tierRoman':'VIII','marks':0,'percent':'57.39','percentRaw':57.39,'avg':'2 159','avgRaw':2159,'source':'exact','region':'eu','regionalMissing':False,'predictionEstimated':True,'session':{'n':2,'avg':'2500','delta':'+0.12'},'steps':[{'p':p,'need':str(n),'g':0,'done':0,'next':int(p==65)} for p,n in [(65,2440),(85,3353),(95,4051),(100,4618)]],'look':{},'goal':{'p':65,'n':20,'g':0,'need':'3000'},'log':[],'mastery':[],'over':0}

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':2048,'height':1152})
    errors=[];page.on('pageerror',lambda err:errors.append(str(err)))
    page.route('**/*',lambda route:route.abort())
    page.set_content('<html><head></head><body></body></html>')
    page.add_style_tag(content=(ASSETS/'panel.css').read_text()+'\n'+(ASSETS/'preview.css').read_text())
    page.evaluate('''data=>{
      window.actions=[];window.fixture=data;
      window.fakeModel={ModInjectModel:{name:'mashkaMarks'},data:JSON.stringify(data),onAction:action=>window.actions.push(action)};
      window.subViews={ids:()=>[1],get:()=>({model:window.fakeModel})};
    }''',fixture)
    page.add_script_tag(content=asset('preview.js'))
    page.add_script_tag(content=asset('panel.js'))
    page.locator('#mmLook').wait_for()
    page.locator('#mmLook').click()
    page.wait_for_timeout(100)
    if baseline:
        assert any('window.mmFrame is not a function' in e for e in errors),errors
        # The constructor aborts before mmLookX gets its click handler.
        page.locator('#mmLookX').click()
        assert page.locator('#mashkaMarksLook').get_attribute('class')!='mm-off'
        print('Baseline reproduced: mmFrame exception; appearance X fails to close.')
        browser.close();sys.exit(0)
    assert not errors,errors
    page.locator('#mmLookX').click()
    assert page.locator('#mashkaMarksLook').get_attribute('class')=='mm-off'
    counts=[]
    for i in range(30):
        page.locator('#mmLook').click()
        assert page.locator('#mashkaMarksLook').get_attribute('class')!='mm-off'
        # Switch tabs, rebuilding all the controls and their handlers.
        for tab in ('hangar','battle'):
            target=page.locator('[data-tab="'+tab+'"]')
            if target.count():target.first.click()
        page.locator('#mmLookX').click()
        assert page.locator('#mashkaMarksLook').get_attribute('class')=='mm-off'
        counts.append(page.evaluate('window.mmTestStats().listeners'))
    assert max(counts[10:])-min(counts[10:])<=4,counts
    print('Settings listener counts after pruning:',counts[0],counts[9],counts[19],counts[29])
    page.locator('#mmLook').click()
    header=page.locator('#mashkaMarksLook .ml-head')
    if not header.count():header=page.locator('#mashkaMarksLook').locator('xpath=./*').first
    box=header.bounding_box();page.mouse.move(box['x']+30,box['y']+10);page.mouse.down();page.mouse.move(box['x']+90,box['y']+40,steps=8);page.mouse.up()
    page.locator('#mmLookX').click()
    assert page.locator('#mashkaMarksLook').get_attribute('class')=='mm-off'
    # History window has its own close path, delayed destructive actions, scrolling.
    page.locator('#mmHist').click()
    page.locator('#mmWinX').click()
    assert page.locator('#mashkaMarksWin').get_attribute('class')=='mm-off'
    # Repeated model updates exercise draw wrappers and stale-control pruning.
    for i in range(10):
        page.evaluate('(i)=>{fixture.percent=(57+i/100).toFixed(2);fakeModel.data=JSON.stringify(fixture)}',i)
        page.wait_for_timeout(320)
    page.evaluate('window.MM_CLEANUP_panel();window.MM_CLEANUP_preview()')
    assert not errors,errors
    assert page.evaluate('window.mmTestStats()')=={'listeners':0,'timers':0,'frames':0}
    browser.close()
    print('Full UI passed: open/close, 30 repeated tab/open/close cycles, drag, history close, model refresh, cleanup; no JS exceptions.')
