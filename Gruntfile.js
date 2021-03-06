module.exports = function(grunt) {

  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-contrib-cssmin');
  grunt.loadNpmTasks('grunt-contrib-uglify');

  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),

    copy: {
      bower: {
        files: [
          {
            expand: true,
            flatten: true,
            src: ['bower_components/components-font-awesome/fonts/*'],
            dest: 'opwen_email_client/webapp/static/fonts/',
            filter: 'isFile'
          },
          {
            expand: true,
            flatten: true,
            src: ['bower_components/bootstrap/fonts/*'],
            dest: 'opwen_email_client/webapp/static/fonts/',
            filter: 'isFile'
          },
          {
            expand: true,
            flatten: true,
            src: [
              'bower_components/flag-icon-css/flags/4x3/ca.svg',
              'bower_components/flag-icon-css/flags/4x3/cd.svg',
              'bower_components/flag-icon-css/flags/4x3/pt.svg',
              'bower_components/flag-icon-css/flags/4x3/tz.svg',
              'bower_components/flag-icon-css/flags/4x3/fr.svg',
            ],
            dest: 'opwen_email_client/webapp/static/flags/4x3/'
          },
          {
            expand: true,
            flatten: true,
            src: [
              'bower_components/jquery/dist/jquery.min.js',
              'bower_components/bootstrap/dist/js/bootstrap.min.js',
              'bower_components/bootstrap-fileinput/js/fileinput.min.js',
              'bower_components/bootstrap3-wysihtml5-bower/dist/bootstrap3-wysihtml5.all.min.js',
            ],
            dest: 'opwen_email_client/webapp/static/js/'
          },
          {
            expand: true,
            flatten: true,
            src: [
              'bower_components/components-font-awesome/css/font-awesome.min.css',
              'bower_components/flag-icon-css/css/flag-icon.min.css',
              'bower_components/bootstrap/dist/css/bootstrap.min.css',
              'bower_components/bootstrap-fileinput/css/fileinput.min.css',
              'bower_components/bootstrap3-wysihtml5-bower/dist/bootstrap3-wysihtml5.min.css',
            ],
            dest: 'opwen_email_client/webapp/static/css/'
          },
        ]
      }
    },

    cssmin: {
      options: {
        shorthandCompacting: false,
        roundingPrecision: -1
      },
      target: {
        files: {
          'opwen_email_client/webapp/static/css/_base_email.min.css': [
            'opwen_email_client/webapp/static/css/_base_email.css',
          ],
          'opwen_email_client/webapp/static/css/about.min.css': [
            'opwen_email_client/webapp/static/css/about.css',
          ],
          'opwen_email_client/webapp/static/css/home.min.css': [
            'opwen_email_client/webapp/static/css/home.css',
          ]
        }
      }
    },

    uglify: {
      bower: {
        options: {
          mangle: true,
          compress: true,
        },
        files: {
          'opwen_email_client/webapp/static/js/printThis.min.js': [
            'bower_components/printThis/printThis.js',
          ]
        }
      },
      app: {
        options: {
          mangle: true,
          compress: true,
        },
        files: {
          'opwen_email_client/webapp/static/js/_base_email.min.js': [
            'opwen_email_client/webapp/static/js/_base_email.js',
          ],
          'opwen_email_client/webapp/static/js/email_new.min.js': [
            'opwen_email_client/webapp/static/js/email_new.js',
          ],
          'opwen_email_client/webapp/static/js/register.min.js': [
            'opwen_email_client/webapp/static/js/register.js',
          ]
        }
      }
    }

  });

  grunt.registerTask('default', [
    'copy:bower',
    'cssmin',
    'uglify:bower',
    'uglify:app'
  ])
};
