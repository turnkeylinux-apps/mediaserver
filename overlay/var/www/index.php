<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">

<html lang="en">
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <meta http-equiv="Content-Style-Type" content="text/css">
        <meta http-equiv="Content-Script-Type" content="text/javascript">

        <title>TurnKey Mediaserver</title>
        
        <link rel="stylesheet" href="css/ui.tabs.css" type="text/css" media="print, projection, screen"/>
        <link rel="stylesheet" href="css/base.css" type="text/css"/>

        <script src="js/jquery-1.2.6.js" type="text/javascript"></script>
        <script src="js/ui.core.js" type="text/javascript"></script>
        <script src="js/ui.tabs.js" type="text/javascript"></script>
        <script type="text/javascript">
            $(function() {
                $('#container-1 > ul').tabs({ fx: { opacity: 'toggle'} });
            });
        </script>
    </head>

    <body>
        <h1>TurnKey Mediaserver</h1>
        
        <div id="container-1">
            <ul>
                <li><a href="#cp"><span>Control Panel</span></a></li>
            </ul>

            <div id="cp">
                <div class="fragment-content" style="left:50%;margin:0 auto">
                    <div style="float:left;width:12%"></div>
                    <div style="float:left;width:20%">
                        <a href="https://<?php print
                        $_SERVER{'HTTP_HOST'}; ?>:12320"><img
                        src="images/shell.png"/>Web Shell</a>
                    </div>
                    <div style="float:left;width:20%">
                        <a href="https://<?php print
                        $_SERVER{'HTTP_HOST'}; ?>:12321"><img
                        src="images/webmin.png"/>Webmin</a>
                    </div>
                    <div style="float:left;width:20%">
                        <a href="https://<?php print
                        $_SERVER{'HTTP_HOST'}; ?>:443"><img
                        src="images/filemanager.png"/>File Manager<br/>(WebDAV)</a>
                    </div>
                    <div style="float:left;width:13%"></div>

                    <div style="float:left;width:20%">
                        <a href="https://<?php print
                        $_SERVER{'HTTP_HOST'}; ?>:12321/samba/index.cgi">
                        <img src="images/samba.png"/>Samba<br/>(via webmin)</a>
                    </div>
                    <div style="float:left;width:20%">
                        <a href="http://<?php print
                        $_SERVER{'HTTP_HOST'}; ?>:8096"><img
                        src="images/emby.png"/>Emby<br/>(HTTP)</a>
                    </div>
                    <div style="float:left;width:20%">
                        <a href="https://<?php print
                        $_SERVER{'HTTP_HOST'}; ?>:8920"><img
                        src="images/emby.png"/>Emby<br />(HTTPS)</a>
                    </div>
                    <div style="float:left;width:10%"></div>
                    <div style="float:left;width:10%"></div>
                    <div style="float:left;width:65%">
                        <h2>Resources and references</h2>
                        <ul>
                            <li>
                               <a href="https://github.com/MediaBrowser/Wiki/wiki">
                               Emby documentation</a>
                            </li>
                            <li>
                               <a href="http://samba.org/samba/docs">
                               Samba documentation</a>
                            </li>
                            <li>
                              <a href="http://www.turnkeylinux.org/mediaserver">
                              TurnKey Mediaserver release notes</a>
                            </li>
                        </ul>
                    </div>
    
                </div>
            </div>

        </div>
    </body>
</html>
