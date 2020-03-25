import { expect as expectCDK, matchTemplate, MatchStyle } from '@aws-cdk/assert';
import * as cdk from '@aws-cdk/core';
import ImagesBack = require('../lib/images-back-stack');

test('Empty Stack', () => {
    const app = new cdk.App();
    // WHEN
    const stack = new ImagesBack.ImagesBackStack(app, 'MyTestStack');
    // THEN
    expectCDK(stack).to(matchTemplate({
      "Resources": {}
    }, MatchStyle.EXACT))
});
