// Capture actual packaged cards at phone width; requires Playwright and Chrome.
const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{
 const root=path.resolve(__dirname,'..'),out=path.join(root,'assets/genki1/samples');fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 try {
  const page=await browser.newPage({viewport:{width:450,height:1100},deviceScaleFactor:2});
  await page.goto('file://'+path.join(root,'experiments/image-production/packaged.html'));
  await page.locator('#phone').check();
  const samples=[['読む','lesson-03-reading'],['住む','lesson-07-living'],['二日酔い','lesson-12-hangover'],['猫','lesson-04-cat'],['急ぐ','hurry'],['飼う','keep-a-pet'],['緊張する','nervous'],['前','in-front'],['取る','take-a-class'],['スマホ','smartphone'],['新幹線','bullet-train']];
  for(const [word,name] of samples){
   const options=await page.locator('#sample option').allTextContents();
   const value=options.findIndex(t=>t==='GENKI I Vocab · '+word);assert(value>=0,word);
   await page.locator('#sample').selectOption(String(value));
   await page.waitForTimeout(200);
   if(['猫','スマホ','新幹線'].includes(word)){
    const question=page.frames().find(f=>f.parentFrame());
    assert.equal(await question.locator('.image-production-question').count(),1,word+' image question');
    assert.equal(await question.locator('.front-english').isVisible(),false,word+' hidden English');
    await page.locator('#frame').screenshot({path:path.join(out,name+'-question.png')});
   }
   await page.locator('#flip').click();await page.waitForTimeout(1400);
   const frame=page.frames().find(f=>f.parentFrame());
   assert(frame,word);assert.equal(await frame.locator('.ex-item').count(),2,word);
   const images=await frame.locator('img').evaluateAll(xs=>xs.every(x=>x.complete&&x.naturalWidth>0));assert(images,word+' artwork');
   await page.locator('#frame').screenshot({path:path.join(out,name+'.png')});
   assert.equal(await frame.locator('.k-box:not(.has-svg)').count(),0,word+' stroke data loaded');
   if(['急ぐ','飼う','新幹線'].includes(word)){
    await page.emulateMedia({colorScheme:'dark'});
    await frame.locator('body').evaluate(el=>el.classList.add('nightMode'));
    await page.waitForTimeout(100);
    await page.locator('#frame').screenshot({path:path.join(out,name+'-dark.png')});
    await frame.locator('body').evaluate(el=>el.classList.remove('nightMode'));
    await page.emulateMedia({colorScheme:'light'});
   }
   console.log('Captured',word,'two examples; images and stroke data loaded');
  }
  await page.close();
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
