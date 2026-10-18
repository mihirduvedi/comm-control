import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import ts from 'typescript';
const source=fs.readFileSync(new URL('../src/format.ts',import.meta.url),'utf8');const code=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext}}).outputText;
const {miles,feet}=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));
test('route totals and short steps retain useful imperial precision',()=>{assert.equal(miles(1609.344),'1.0 mi');assert.equal(miles(16093.44),'10.0 mi');assert.equal(miles(805),'0.5 mi');assert.equal(miles(1,true),'<0.01 mi');assert.equal(miles(0),'0.0 mi')});
test('location accuracy rounds outward instead of claiming extra precision',()=>{assert.equal(feet(10),'33 ft');assert.equal(feet(0.3048),'1 ft');assert.equal(feet(Number.NaN),'unknown');assert.equal(miles(-1),'Unavailable')});
