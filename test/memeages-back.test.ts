import { expect as expectCDK, matchTemplate, MatchStyle } from '@aws-cdk/assert';
import * as cdk from '@aws-cdk/core';
import MemeagesBack = require('../lib/memeages-back-stack');

test('Empty Stack', () => {
    const app = new cdk.App();
    // WHEN
    const stack = new MemeagesBack.MemeagesBackStack(app, 'MyTestStack');
    // THEN
    expectCDK(stack).to(matchTemplate({
      "Resources": {}
    }, MatchStyle.EXACT))
});
