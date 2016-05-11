// Karma configuration
// Generated on Tue Dec 01 2015 09:58:18 GMT+1300 (NZDT)

// For manually testing use
// karma start tests/karma-auto.conf.js --no-single-run --reporters progress

module.exports = function(config) {
  config.set({

    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: '..',

    // frameworks to use
    // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
    frameworks: ['jasmine'],

    // list of files / patterns to load in the browser
    files: [
      // It's important that these are in order for dependencies?
      'static/js/vendor/jquery.min.js',
      'http://ajax.googleapis.com/ajax/libs/angularjs/1.4.5/angular.js',
      'http://ajax.googleapis.com/ajax/libs/angularjs/1.4.5/angular-resource.js',
      'http://ajax.googleapis.com/ajax/libs/angularjs/1.4.5/angular-route.js',
      'http://ajax.googleapis.com/ajax/libs/angularjs/1.4.5/angular-mocks.js',

      // Extra javascript which is only used for testing.
      'tests/client/includes/*.js',

      // TODO will need to add everything here.
      // EightI player API.
      'static/js/eighti/eighti.min.js',
      {pattern: 'static/js/eighti/eighti.lib.js.mem', included: false},

      // Common setup code.
      // TODO should we use separate conf files per feature?
      'static/three.min.js',
      'static/8i.utils.js',
      'static/ua-parser.min.js',
      'static/js/playerSettings.js',
      'static/8i.controls.js',
      'static/js/eighti/dahparser.js',
      'static/js/player2cardboard.js',
      'static/js/DeviceOrientationControls.js',
      'static/js/StereoEffect.js',
      'static/js/overlay3d.js',


      // Cardboard app
      'static/angular/cardboard/*.js',

      // Web Director app
      'static/three-js/loaders/OBJLoader.js',
      'static/angular/director/*.js',
      'static/js/threejs/helvetiker_bold.typeface.js',
      'static/angular/scene/*.js',

      // Admin angular apps.
      'static/angular/admin/*.js',
      'static/angular/new_admin/*.js',

      // Angular player app.
      'static/angular/new_player/*.js',
      // Used by player app.
      'static/new_site/8iTemplate.js',

      // Angular app for the new 8i site.
      'static/angular/player/playerControls.js',
      'static/new_site/8i.js',

      // Player 2, needed after playerControls which designates the path.
      'static/js/eighti/eighti.lib.js',

      {pattern: 'static/img/backgroundScenes/venice_beach2.jpg', included:false},

      // Lastly include the tests.
      'tests/client/admin/*_spec.js',
      'tests/client/*_spec.js',

      // Include example scenes for testing.
      { pattern:  'static/sceneExamples/*.json',
        watched:  true,
        served:   true,
        included: false }
    ],

    proxies: {
      // Make sure static files are found correctly.
      "/static/": "http://localhost:9878/base/static/"
    },

    // test results reporter to use
    // possible values: 'dots', 'progress'
    // available reporters: https://npmjs.org/browse/keyword/karma-reporter
    reporters: ['json'],

    // For saving and storing results.
    // Also requires the bug fix in https://github.com/douglasduteil/karma-json-reporter/issues/13
    jsonReporter: {
      stdout: false,
      outputFile: 'results.json' // defaults to none
    },

    // start these browsers
    // available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
    browsers: ['PhantomJS'],

    // Use a port which is different to normal so I can run local karma without trouble.
    port: 9878,

    // Continuous Integration mode
    // if true, Karma captures browsers, runs the tests and exits
    singleRun: true,
  })
}
