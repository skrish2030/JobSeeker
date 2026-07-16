function handler(event) {
    var request = event.request;
    var clientIP = event.viewer.ip;
    
    // Whitelisted IPs: populated dynamically by Terraform templatefile
    var whitelist = [${whitelisted_ips_json}];
    
    // If whitelist is empty or contains "0.0.0.0/0", allow access
    if (whitelist.length === 0 || whitelist.indexOf("0.0.0.0/0") !== -1) {
        return request;
    }
    
    var allowed = false;
    for (var i = 0; i < whitelist.length; i++) {
        var cidr = whitelist[i];
        if (cidr === clientIP) {
            allowed = true;
            break;
        }
        
        // Match simple CIDR ranges
        if (cidr.indexOf('/') !== -1) {
            var parts = cidr.split('/');
            var baseIP = parts[0];
            var mask = parseInt(parts[1], 10);
            
            if (mask === 32 && baseIP === clientIP) {
                allowed = true;
                break;
            }
            
            // Fast octet check for /24 (e.g. 192.168.1.0/24)
            if (mask === 24) {
                var clientOctets = clientIP.split('.');
                var baseOctets = baseIP.split('.');
                if (clientOctets[0] === baseOctets[0] && 
                    clientOctets[1] === baseOctets[1] && 
                    clientOctets[2] === baseOctets[2]) {
                    allowed = true;
                    break;
                }
            }
            
            // Fast octet check for /16 (e.g. 172.16.0.0/16)
            if (mask === 16) {
                var clientOctets = clientIP.split('.');
                var baseOctets = baseIP.split('.');
                if (clientOctets[0] === baseOctets[0] && 
                    clientOctets[1] === baseOctets[1]) {
                    allowed = true;
                    break;
                }
            }
        }
    }
    
    if (allowed) {
        return request;
    }
    
    // Otherwise return 403 Forbidden
    return {
        statusCode: 403,
        statusDescription: 'Forbidden',
        headers: {
            'content-type': { value: 'text/html' }
        },
        body: '<!DOCTYPE html><html><head><title>Access Denied</title><style>body{font-family:system-ui,sans-serif;background:#0f172a;color:#f8fafc;display:flex;flex-direction:column;align-items:center;justify-content:center;height:90vh;margin:0}h1{font-size:3rem;margin:0;background:linear-gradient(135deg,#f43f5e,#e11d48);-webkit-background-clip:text;-webkit-text-fill-color:transparent}p{color:#94a3b8;font-size:1.1rem;margin-top:10px}</style></head><body><h1>403 Access Denied</h1><p>Your IP address (' + clientIP + ') is not whitelisted.</p></body></html>'
    };
}
