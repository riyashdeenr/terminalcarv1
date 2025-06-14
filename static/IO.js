        const term = new Terminal();
        term.open(document.getElementById('terminal'));

        const socket = io();

        // Display output from backend
        socket.on('app_output', function(data) {
            term.write(data.output);
        });

        // Buffer input and send only on ENTER
        let inputBuffer = '';
        term.onData(function(data) {
            if (data === '\r') {
                term.write('\r\n');
                socket.emit('app_input', { input: inputBuffer });
                inputBuffer = '';
            } else if (data === '\u007F') { // Backspace
                if (inputBuffer.length > 0) {
                    term.write('\b \b');
                    inputBuffer = inputBuffer.slice(0, -1);
                }
            } else {
                term.write(data);
                inputBuffer += data;
            }
        });